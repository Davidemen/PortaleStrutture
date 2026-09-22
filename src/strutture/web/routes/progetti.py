"""API routes for projects and saved elements (`docs/architecture-phase3.md`).

The repository is injected as a `ProjectRepository` Protocol (tests use a small in-memory fake,
never the real SQLite module). Export/import delegate to `strutture.storage.scambio`, imported
lazily inside `_scambio_esporta` / `_scambio_importa` -- that module is written by another agent
in parallel, so importing it at module load time would break every web test (including this
file's own) until it lands, exactly like the sign-off SQLite repository in `app.py`."""
import logging
from typing import Any, Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from strutture.shared.tool import Tool
from strutture.storage.interfaces import ConflictError, NotFoundError, ProjectRepository
from strutture.storage.models import (
    MAX_NOME,
    MAX_NOTA,
    MAX_NOTE,
    MAX_SIGLA,
    Elemento,
    Progetto,
    StatoElemento,
)

from ..envelope import error_envelope

logger = logging.getLogger(__name__)

_CONFLICT_IT = "Modificato da un altro utente: ricarica e riprova"
_MAX_CODICE = 40
_MAX_STRUMENTO = 80


def build_progetti_router(progetti: ProjectRepository, tools: dict[str, Tool]) -> APIRouter:
    """Build the `/api/progetti` and `/api/elementi` routers bound to a fixed repository and the
    tool registry (used to validate `strumento` on element creation)."""
    router = APIRouter()
    _register_progetti_read_routes(router, progetti)
    _register_progetti_create_route(router, progetti)
    _register_progetti_update_route(router, progetti)
    _register_progetti_delete_routes(router, progetti)
    _register_elementi_read_routes(router, progetti)
    _register_elementi_create_route(router, progetti, tools)
    _register_elementi_update_route(router, progetti, tools)
    _register_elementi_lifecycle_routes(router, progetti)
    _register_scambio_routes(router, progetti, tools)
    return router


# ---- progetti ----


def _register_progetti_read_routes(router: APIRouter, progetti: ProjectRepository) -> None:
    @router.get("/api/progetti")
    def list_progetti(inclusi_eliminati: bool = False) -> list[dict[str, Any]]:
        return [p.model_dump(mode="json") for p in progetti.list_progetti(inclusi_eliminati=inclusi_eliminati)]

    @router.get("/api/progetti/{progetto_id}")
    def get_progetto(progetto_id: str) -> Any:
        try:
            return progetti.get_progetto(progetto_id).model_dump(mode="json")
        except NotFoundError:
            return _not_found_progetto(progetto_id)


def _register_progetti_create_route(router: APIRouter, progetti: ProjectRepository) -> None:
    @router.post("/api/progetti")
    async def crea_progetto(request: Request) -> Any:
        body = await _parse_body(request, _ProgettoBody)
        if isinstance(body, JSONResponse):
            return body
        created = progetti.crea_progetto(
            Progetto(codice=body.codice, nome=body.nome, committente=body.committente, note=body.note)
        )
        return JSONResponse(created.model_dump(mode="json"), status_code=201)


def _register_progetti_update_route(router: APIRouter, progetti: ProjectRepository) -> None:
    @router.put("/api/progetti/{progetto_id}")
    async def aggiorna_progetto(progetto_id: str, request: Request) -> Any:
        body = await _parse_body(request, _ProgettoUpdateBody)
        if isinstance(body, JSONResponse):
            return body
        candidate = Progetto(
            id=progetto_id,
            codice=body.codice,
            nome=body.nome,
            committente=body.committente,
            note=body.note,
            revisione=body.revisione,
        )
        try:
            saved = progetti.aggiorna_progetto(candidate)
        except ConflictError:
            return _conflict(progetti, progetto_id, "progetto")
        except NotFoundError:
            return _not_found_progetto(progetto_id)
        return saved.model_dump(mode="json")


def _register_progetti_delete_routes(router: APIRouter, progetti: ProjectRepository) -> None:
    @router.delete("/api/progetti/{progetto_id}")
    async def elimina_progetto(progetto_id: str, request: Request) -> Any:
        body = await _parse_body(request, _RevisioneBody)
        if isinstance(body, JSONResponse):
            return body
        try:
            progetti.elimina_progetto(progetto_id, body.revisione)
        except ConflictError:
            return _conflict(progetti, progetto_id, "progetto")
        except NotFoundError:
            return _not_found_progetto(progetto_id)
        return {"eliminato": True}

    @router.post("/api/progetti/{progetto_id}/ripristina")
    def ripristina_progetto(progetto_id: str) -> Any:
        try:
            return progetti.ripristina_progetto(progetto_id).model_dump(mode="json")
        except NotFoundError:
            return _not_found_progetto(progetto_id)


# ---- elementi ----


def _register_elementi_read_routes(router: APIRouter, progetti: ProjectRepository) -> None:
    @router.get("/api/progetti/{progetto_id}/elementi")
    def list_elementi(progetto_id: str, inclusi_eliminati: bool = False) -> Any:
        try:
            elementi = progetti.list_elementi(progetto_id, inclusi_eliminati=inclusi_eliminati)
        except NotFoundError:
            return _not_found_progetto(progetto_id)
        return [e.model_dump(mode="json") for e in elementi]

    @router.get("/api/elementi/{elemento_id}")
    def get_elemento(elemento_id: str) -> Any:
        try:
            return progetti.get_elemento(elemento_id).model_dump(mode="json")
        except NotFoundError:
            return _not_found_elemento(elemento_id)

    @router.get("/api/elementi/{elemento_id}/revisioni")
    def revisioni(elemento_id: str) -> Any:
        try:
            history = progetti.revisioni(elemento_id)
        except NotFoundError:
            return _not_found_elemento(elemento_id)
        return [r.model_dump(mode="json") for r in history]


def _register_elementi_create_route(router: APIRouter, progetti: ProjectRepository, tools: dict[str, Tool]) -> None:
    @router.post("/api/progetti/{progetto_id}/elementi")
    async def crea_elemento(progetto_id: str, request: Request) -> Any:
        body = await _parse_body(request, _ElementoBody)
        if isinstance(body, JSONResponse):
            return body
        if body.strumento not in tools:
            return error_envelope(f"Strumento sconosciuto: {body.strumento}", 400)
        elemento = Elemento(
            progetto_id=progetto_id,
            strumento=body.strumento,
            nome=body.nome,
            inputs=body.inputs,
            sintesi=body.sintesi,
            stato=body.stato,
            modalita=body.modalita,
            provenienza=body.provenienza,
            versione_app=_versione_app(),
        )
        try:
            created = progetti.crea_elemento(elemento, sigla=body.sigla, nota=body.nota)
        except NotFoundError:
            return _not_found_progetto(progetto_id)
        return JSONResponse(created.model_dump(mode="json"), status_code=201)


def _register_elementi_update_route(router: APIRouter, progetti: ProjectRepository, tools: dict[str, Tool]) -> None:
    @router.put("/api/elementi/{elemento_id}")
    async def aggiorna_elemento(elemento_id: str, request: Request) -> Any:
        body = await _parse_body(request, _ElementoUpdateBody)
        if isinstance(body, JSONResponse):
            return body
        if body.strumento not in tools:
            return error_envelope(f"Strumento sconosciuto: {body.strumento}", 400)
        try:
            current = progetti.get_elemento(elemento_id)
        except NotFoundError:
            return _not_found_elemento(elemento_id)
        candidate = current.model_copy(
            update={
                "strumento": body.strumento,
                "nome": body.nome,
                "inputs": body.inputs,
                "sintesi": body.sintesi,
                "stato": body.stato,
                "modalita": body.modalita,
                "provenienza": body.provenienza,
                "versione_app": _versione_app(),
                "revisione": body.revisione,
            }
        )
        try:
            saved = progetti.aggiorna_elemento(candidate, sigla=body.sigla, nota=body.nota)
        except ConflictError:
            return _conflict_elemento(progetti, elemento_id)
        except NotFoundError:
            return _not_found_elemento(elemento_id)
        return saved.model_dump(mode="json")


def _register_elementi_lifecycle_routes(router: APIRouter, progetti: ProjectRepository) -> None:
    @router.delete("/api/elementi/{elemento_id}")
    async def elimina_elemento(elemento_id: str, request: Request) -> Any:
        body = await _parse_body(request, _RevisioneBody)
        if isinstance(body, JSONResponse):
            return body
        try:
            progetti.elimina_elemento(elemento_id, body.revisione)
        except ConflictError:
            return _conflict_elemento(progetti, elemento_id)
        except NotFoundError:
            return _not_found_elemento(elemento_id)
        return {"eliminato": True}

    @router.post("/api/elementi/{elemento_id}/ripristina")
    def ripristina_elemento(elemento_id: str) -> Any:
        try:
            return progetti.ripristina_elemento(elemento_id).model_dump(mode="json")
        except NotFoundError:
            return _not_found_elemento(elemento_id)

    @router.post("/api/elementi/{elemento_id}/duplica")
    async def duplica_elemento(elemento_id: str, request: Request) -> Any:
        body = await _parse_body(request, _DuplicaBody)
        if isinstance(body, JSONResponse):
            return body
        try:
            duplicated = progetti.duplica_elemento(elemento_id, body.nome)
        except NotFoundError:
            return _not_found_elemento(elemento_id)
        return JSONResponse(duplicated.model_dump(mode="json"), status_code=201)


# ---- export / import ----


def _register_scambio_routes(router: APIRouter, progetti: ProjectRepository, tools: dict[str, Tool]) -> None:
    @router.get("/api/progetti/{progetto_id}/esporta")
    def esporta(progetto_id: str) -> Any:
        try:
            progetto = progetti.get_progetto(progetto_id)
        except NotFoundError:
            return _not_found_progetto(progetto_id)
        elementi_con_revisioni = tuple(
            (elemento, progetti.revisioni(elemento.id)) for elemento in progetti.list_elementi(progetto_id)
        )
        return _scambio_esporta(progetto, elementi_con_revisioni, _versione_app())

    @router.post("/api/progetti/importa")
    async def importa(request: Request) -> Any:
        try:
            raw = await request.json()
        except ValueError:
            return error_envelope("Corpo della richiesta non è un JSON valido.", 400)
        if not isinstance(raw, dict):
            return error_envelope("Il corpo della richiesta deve essere un oggetto JSON.", 400)
        try:
            progetto, avvisi = _scambio_importa(raw, progetti, frozenset(tools))
        except ValueError as error:
            return error_envelope(str(error), 400)
        return {"progetto": progetto.model_dump(mode="json"), "avvisi": list(avvisi)}


def _scambio_esporta(progetto: Progetto, elementi_con_revisioni: Any, versione_app: str) -> dict[str, Any]:
    from strutture.storage import scambio

    return scambio.esporta(progetto, elementi_con_revisioni, versione_app)


def _scambio_importa(
    payload: dict[str, Any], repository: ProjectRepository, strumenti_noti: frozenset[str]
) -> tuple[Progetto, tuple[str, ...]]:
    from strutture.storage import scambio

    return scambio.importa(payload, repository, strumenti_noti)


def _versione_app() -> str:
    import strutture

    return getattr(strutture, "__version__", "0.1.0")


class _ProgettoBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    codice: str = Field(default="", max_length=_MAX_CODICE)
    nome: str = Field(min_length=1, max_length=MAX_NOME)
    committente: str = Field(default="", max_length=MAX_NOME)
    note: str = Field(default="", max_length=MAX_NOTE)


class _ProgettoUpdateBody(_ProgettoBody):
    revisione: int = Field(ge=0)


class _ElementoBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    strumento: str = Field(min_length=1, max_length=_MAX_STRUMENTO)
    nome: str = Field(min_length=1, max_length=MAX_NOME)
    inputs: dict[str, Any] = Field(default_factory=dict)
    sintesi: dict[str, Any] = Field(default_factory=dict)
    stato: StatoElemento = "non_verificato"
    modalita: Literal["standard", "excel"] = "standard"
    provenienza: dict[str, Any] = Field(default_factory=dict)
    sigla: str = Field(default="", max_length=MAX_SIGLA)
    nota: str = Field(default="", max_length=MAX_NOTA)


class _ElementoUpdateBody(_ElementoBody):
    revisione: int = Field(ge=0)


class _RevisioneBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    revisione: int = Field(ge=0)


class _DuplicaBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    nome: str = Field(min_length=1, max_length=MAX_NOME)


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


def _not_found_progetto(progetto_id: str) -> JSONResponse:
    return error_envelope(f"Progetto sconosciuto: {progetto_id}", 404)


def _not_found_elemento(elemento_id: str) -> JSONResponse:
    return error_envelope(f"Elemento sconosciuto: {elemento_id}", 404)


def _conflict(progetti: ProjectRepository, progetto_id: str, _kind: str) -> JSONResponse:
    try:
        current = progetti.get_progetto(progetto_id)
    except NotFoundError:
        return _not_found_progetto(progetto_id)
    return _conflict_envelope(current)


def _conflict_elemento(progetti: ProjectRepository, elemento_id: str) -> JSONResponse:
    try:
        current = progetti.get_elemento(elemento_id)
    except NotFoundError:
        return _not_found_elemento(elemento_id)
    return _conflict_envelope(current)


def _conflict_envelope(current: BaseModel) -> JSONResponse:
    body = {
        "ok": False,
        "data": None,
        "checks": [],
        "warnings": [],
        "errors": [_CONFLICT_IT],
        "inputs_echo": {},
        "attuale": current.model_dump(mode="json"),
    }
    return JSONResponse(content=body, status_code=409)
