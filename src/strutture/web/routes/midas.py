"""HTTP surface for the MIDAS integration (docs/integrations/MIDAS.md §4). Thin: all logic lives in
`strutture.integrations.midas`; this module only validates requests, builds a client, and maps
`MidasError` onto the `{ok: false, errors, kind}` envelope with the documented status codes."""
import logging
from collections.abc import Callable
from typing import Annotated, Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from strutture.integrations.midas import (
    Combination,
    MidasClient,
    MidasError,
    MidasSettings,
    autodetect_base_url,
    has_server_key,
    probe,
    read_combinations,
    read_reactions,
    read_supports,
    read_units,
    resolve_key,
    suggest_famiglia,
)
from strutture.shared.load_table import Famiglia

logger = logging.getLogger(__name__)

ClientFactory = Callable[[str, str], MidasClient]
_INTERNAL_ERROR_IT = "Si è verificato un errore interno del server. Riprova più tardi."

# HIGH 2 (security review): every list/string in a request body is bounded, so one request can
# never force thousands of MIDAS round trips or gigabytes of JSON.
_MAX_STRING_LENGTH = 200
_MAX_COMBINAZIONI = 500
_MAX_NODI = 5000
_NodeId = Annotated[int, Field(ge=1)]
_BoundedStr = Annotated[str, Field(max_length=_MAX_STRING_LENGTH)]


class _VerifyBody(BaseModel):
    model_config = ConfigDict(frozen=True)
    base_url: _BoundedStr | None = None
    product: Literal["gen", "civil"] | None = None


class _BaseUrlBody(BaseModel):
    model_config = ConfigDict(frozen=True)
    base_url: _BoundedStr | None = None


class _ComboSelection(BaseModel):
    model_config = ConfigDict(frozen=True)
    table_name: str = Field(min_length=1, max_length=_MAX_STRING_LENGTH)
    famiglia: Famiglia | None = None


class _ReactionsBody(BaseModel):
    model_config = ConfigDict(frozen=True)
    base_url: _BoundedStr | None = None
    nodi: tuple[_NodeId, ...] = Field(default=(), max_length=_MAX_NODI)
    gruppo: _BoundedStr | None = None
    combinazioni: tuple[_ComboSelection, ...] = Field(min_length=1, max_length=_MAX_COMBINAZIONI)


def build_midas_router(*, client_factory: ClientFactory | None = None) -> APIRouter:
    """`client_factory(base_url, key) -> MidasClient` defaults to a real httpx-backed client;
    tests inject one bound to `httpx.MockTransport`."""
    make_client = client_factory or _default_client_factory
    router = APIRouter(prefix="/api/midas")

    @router.get("/status")
    def status() -> dict:
        settings = MidasSettings.from_env()
        return {"server_key": has_server_key(), "base_url": settings.base_url, "product": settings.product}

    @router.post("/verify")
    async def verify(request: Request) -> JSONResponse:
        return await _run(request, _VerifyBody, lambda body, key: _verify(body, key, make_client))

    @router.post("/combinations")
    async def combinations(request: Request) -> JSONResponse:
        return await _run(request, _BaseUrlBody, lambda body, key: _combinations(body, key, make_client))

    @router.post("/supports")
    async def supports(request: Request) -> JSONResponse:
        return await _run(request, _BaseUrlBody, lambda body, key: _supports(body, key, make_client))

    @router.post("/reactions")
    async def reactions(request: Request) -> JSONResponse:
        return await _run(request, _ReactionsBody, lambda body, key: _reactions(body, key, make_client))

    return router


def _default_client_factory(base_url: str, key: str) -> MidasClient:
    return MidasClient(base_url, key, allowed_hosts=MidasSettings.from_env().allowed_hosts)


async def _run(request: Request, model: type[BaseModel], handler: Callable[[BaseModel, str], JSONResponse]) -> JSONResponse:
    """Shared plumbing for every POST route: parse the body, resolve the key, run the handler and
    map any `MidasError` (or an unexpected bug) onto the response envelope."""
    body = await _parse_body(request, model)
    if isinstance(body, JSONResponse):
        return body
    key = resolve_key(request.headers.get("X-Midas-Key"))
    if not key:
        return _error(MidasError("auth", "Nessuna chiave MAPI disponibile. Inserisci la chiave o imposta MIDAS_MAPI_KEY sul server."))
    try:
        # `handler` makes synchronous httpx calls to MIDAS; off-load it to FastAPI's threadpool so
        # one slow/large request never blocks the event loop (and every other concurrent request).
        return await run_in_threadpool(handler, body, key)
    except MidasError as error:
        return _error(error)
    except Exception:
        logger.exception("unexpected error in a MIDAS route")
        return JSONResponse({"ok": False, "errors": [_INTERNAL_ERROR_IT], "kind": "bad_response"}, status_code=500)


async def _parse_body(request: Request, model: type[BaseModel]) -> BaseModel | JSONResponse:
    try:
        raw = await request.json()
    except ValueError:
        return _error(MidasError("forbidden_url", "Corpo della richiesta non è un JSON valido."))
    if not isinstance(raw, dict):
        return _error(MidasError("forbidden_url", "Il corpo della richiesta deve essere un oggetto JSON."))
    try:
        return model.model_validate(raw)
    except ValidationError as validation_error:
        message = validation_error.errors()[0]["msg"]
        return _error(MidasError("forbidden_url", f"Corpo della richiesta non valido: {message}"))


def _error(error: MidasError) -> JSONResponse:
    return JSONResponse({"ok": False, "errors": [error.message_it], "kind": error.kind}, status_code=error.status_code)


def _verify(body: _VerifyBody, key: str, make_client: ClientFactory) -> JSONResponse:
    if body.base_url:
        client = make_client(body.base_url, key)
        base_url = body.base_url
        info = probe(client)
    else:
        base_url, client, info = autodetect_base_url(lambda url: make_client(url, key), body.product or "gen")
    force, dist = read_units(client)
    return JSONResponse(
        {
            "ok": True,
            "product": info.product,
            "name": info.name,
            "version": info.version,
            "base_url": base_url,
            "units": {"force": force, "dist": dist},
        }
    )


def _combinations(body: _BaseUrlBody, key: str, make_client: ClientFactory) -> JSONResponse:
    client = make_client(_resolve_base_url(body.base_url), key)
    combos = read_combinations(client)
    return JSONResponse({"combinations": [_combo_json(combo) for combo in combos]})


def _combo_json(combo: Combination) -> dict:
    return {
        "name": combo.name,
        "table_name": combo.table_name,
        "classification": combo.classification,
        "active": combo.active,
        "description": combo.description,
        "famiglia_suggerita": suggest_famiglia(combo),
    }


def _supports(body: _BaseUrlBody, key: str, make_client: ClientFactory) -> JSONResponse:
    client = make_client(_resolve_base_url(body.base_url), key)
    nodes = read_supports(client)
    return JSONResponse({"supports": [{"nodo": n.nodo, "x_m": n.x_m, "y_m": n.y_m, "z_m": n.z_m} for n in nodes]})


def _reactions(body: _ReactionsBody, key: str, make_client: ClientFactory) -> JSONResponse:
    client = make_client(_resolve_base_url(body.base_url), key)
    righe, avvisi = read_reactions(
        client,
        combinazioni=tuple((c.table_name, c.famiglia) for c in body.combinazioni),
        nodi=body.nodi,
        gruppo=body.gruppo,
    )
    return JSONResponse(
        {"righe": [row.model_dump(mode="json") for row in righe], "n_righe": len(righe), "avvisi": list(avvisi)}
    )


def _resolve_base_url(body_base_url: str | None) -> str:
    base_url = body_base_url or MidasSettings.from_env().base_url
    if not base_url:
        raise MidasError("forbidden_url", "Specificare base_url: nessun valore di default configurato sul server.")
    return base_url
