"""API routes for the divergence register and its sign-off workflow (roadmap Phase 1.2).

Business data comes from `strutture.shared.divergences.load_register()` (the JSON files) merged,
per id, with the current `Signoff` from a `SignoffRepository`. Both are injected so tests never
touch the real files or a real database."""
import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from strutture.shared.divergences.loader import load_register
from strutture.shared.divergences.models import Divergence
from strutture.shared.divergences.riepilogo import STATI, riepilogo_per_strumento
from strutture.storage.interfaces import SignoffRepository
from strutture.storage.models import MAX_NOTA, MAX_SIGLA, Signoff, Stato

from ..envelope import error_envelope

logger = logging.getLogger(__name__)

_STATI: tuple[Stato, ...] = ("da_confermare", "approvato", "respinto")
_MAX_BULK_IDS = 200
_SIGLA_REQUIRED_IT = "sigla è obbligatoria per approvare o respingere (1-12 caratteri)"


def build_divergences_router(
    signoffs: SignoffRepository, register: tuple[Divergence, ...] | None = None
) -> APIRouter:
    """Build the `/api/divergences...` router. `register` defaults to the real, packaged register;
    inject a fixed tuple in tests instead."""
    router = APIRouter(prefix="/api/divergences")
    _register_list_routes(router, signoffs, register)
    _register_detail_route(router, signoffs, register)
    _register_signoff_routes(router, signoffs, register)
    return router


def _register_list_routes(
    router: APIRouter, signoffs: SignoffRepository, register: tuple[Divergence, ...] | None
) -> None:
    @router.get("")
    def list_divergences(
        strumento: str | None = None, tipo: str | None = None, stato: str | None = None, q: str | None = None
    ) -> dict[str, Any]:
        entries = [_entry(d, signoffs.get(d.id)) for d in _all_divergences(register)]
        filtered = [e for e in entries if _matches(e, strumento, tipo, stato, q)]
        return {"divergenze": filtered, "totali": _totals(e["stato"] for e in filtered)}

    @router.get("/riepilogo")
    def riepilogo() -> dict[str, Any]:
        completo = riepilogo_per_strumento(_all_divergences(register), signoffs)
        per_strumento = {nome: {s: voce[s] for s in STATI} for nome, voce in completo.items()}
        return {"per_strumento": per_strumento}


def _register_detail_route(
    router: APIRouter, signoffs: SignoffRepository, register: tuple[Divergence, ...] | None
) -> None:
    @router.get("/{unita}/{slug}")
    def get_divergence(unita: str, slug: str) -> Any:
        divergence_id = f"{unita}/{slug}"
        divergence = _by_id(register).get(divergence_id)
        if divergence is None:
            return _unknown_divergence(divergence_id)
        entry = _entry(divergence, signoffs.get(divergence_id))
        history = [s.model_dump(mode="json") for s in signoffs.history(divergence_id)]
        return {**entry, "storia": history}


def _register_signoff_routes(
    router: APIRouter, signoffs: SignoffRepository, register: tuple[Divergence, ...] | None
) -> None:
    @router.put("/{unita}/{slug}/signoff")
    async def signoff(unita: str, slug: str, request: Request) -> Any:
        divergence_id = f"{unita}/{slug}"
        if divergence_id not in _by_id(register):
            return _unknown_divergence(divergence_id)
        body = await _parse_body(request, _SignoffBody)
        if isinstance(body, JSONResponse):
            return body
        stored = signoffs.set(divergence_id, body.stato, body.sigla, body.nota)
        return stored.model_dump(mode="json")

    @router.post("/signoff-multiplo")
    async def signoff_multiplo(request: Request) -> Any:
        body = await _parse_body(request, _BulkSignoffBody)
        if isinstance(body, JSONResponse):
            return body
        known = _by_id(register)
        updated = 0
        for divergence_id in body.ids:
            if divergence_id in known:
                signoffs.set(divergence_id, body.stato, body.sigla, body.nota)
                updated += 1
        return {"aggiornati": updated}


def _all_divergences(register: tuple[Divergence, ...] | None) -> tuple[Divergence, ...]:
    return register if register is not None else load_register()


def _by_id(register: tuple[Divergence, ...] | None) -> dict[str, Divergence]:
    return {d.id: d for d in _all_divergences(register)}


class _SignoffBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    stato: Stato
    sigla: str = Field(default="", max_length=MAX_SIGLA)
    nota: str = Field(default="", max_length=MAX_NOTA)

    @model_validator(mode="after")
    def _sigla_required_unless_pending(self) -> "_SignoffBody":
        if self.stato != "da_confermare" and not (1 <= len(self.sigla) <= MAX_SIGLA):
            raise ValueError(_SIGLA_REQUIRED_IT)
        return self


class _BulkSignoffBody(_SignoffBody):
    ids: tuple[str, ...] = Field(min_length=1, max_length=_MAX_BULK_IDS)


async def _parse_body(request: Request, model: type[BaseModel]) -> BaseModel | JSONResponse:
    try:
        raw = await request.json()
    except ValueError:
        return error_envelope("Corpo della richiesta non è un JSON valido.", 400)
    if not isinstance(raw, dict):
        return error_envelope("Il corpo della richiesta deve essere un oggetto JSON.", 400)
    try:
        return model.model_validate(raw)
    except ValidationError as error:
        messages = [str(e["msg"]).removeprefix("Value error, ") for e in error.errors()]
        return error_envelope("; ".join(messages), 400)


def _entry(divergence: Divergence, signoff: Signoff) -> dict[str, Any]:
    return {
        **divergence.model_dump(mode="json"),
        "stato": signoff.stato,
        "sigla": signoff.sigla,
        "nota": signoff.nota,
        "data": signoff.data,
    }


def _matches(entry: dict[str, Any], strumento: str | None, tipo: str | None, stato: str | None, q: str | None) -> bool:
    if strumento is not None and strumento not in entry["strumenti"]:
        return False
    if tipo is not None and entry["tipo"] != tipo:
        return False
    if stato is not None and entry["stato"] != stato:
        return False
    if q:
        haystack = " ".join((entry["titolo"], entry["foglio"], entry["corretto"], entry["id"])).lower()
        if q.lower() not in haystack:
            return False
    return True


def _totals(stati: Any) -> dict[str, int]:
    counts = {s: 0 for s in _STATI}
    for stato in stati:
        counts[stato] += 1
    return counts


def _unknown_divergence(divergence_id: str) -> JSONResponse:
    return error_envelope(f"Divergenza sconosciuta: {divergence_id}", 404)
