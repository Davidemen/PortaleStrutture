"""API routes for the office settings (WORKBENCH_SPEC.md §26.7)."""
import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from strutture.shared.impostazioni.campi import campi_numerici
from strutture.shared.impostazioni.modelli import FABBRICA, TIPI_DATO, Impostazioni
from strutture.shared.impostazioni.risolvi import passo_proposto
from strutture.shared.impostazioni.tipi_dato import tipo_dato
from strutture.shared.impostazioni.validazione import valida_eccezioni, valida_passi_per_tipo
from strutture.shared.tool import Tool
from strutture.storage.interfaces import ConflictError, ImpostazioniRepository
from strutture.storage.models import MAX_SIGLA

from ..envelope import error_envelope
from ..errori_it import messaggio_errore_it

logger = logging.getLogger(__name__)
_ETICHETTE_TIPO = {
    "lunghezza_m": "Lunghezze in m", "lunghezza_cm": "Lunghezze in cm", "lunghezza_mm": "Lunghezze in mm",
    "diametro_armatura": "Diametri di armatura", "passo_armatura": "Passi di armatura",
    "copriferro": "Copriferri", "spessore": "Spessori", "intero": "Numeri interi",
}


def build_impostazioni_router(repository: ImpostazioniRepository, tools: dict[str, Tool]) -> APIRouter:
    router = APIRouter(prefix="/api/impostazioni")
    _register_read_routes(router, repository, tools)
    _register_write_route(router, repository, tools)
    _register_tipi_route(router, tools)
    _register_passi_route(router, repository, tools)
    return router


def _register_read_routes(router: APIRouter, repository: ImpostazioniRepository, tools: dict[str, Tool]) -> None:
    @router.get("")
    def leggi() -> dict[str, Any]:
        return _stato_attuale(repository, tools)

    @router.get("/storia")
    def storia(limite: int = 50) -> list[dict[str, Any]]:
        return [s.model_dump(mode="json") for s in repository.storia(limite)]


def _register_write_route(router: APIRouter, repository: ImpostazioniRepository, tools: dict[str, Tool]) -> None:
    @router.put("")
    async def salva(request: Request) -> Any:
        body = await _parse_body(request)
        if isinstance(body, JSONResponse):
            return body
        errori_registro = valida_eccezioni(body.impostazioni.passi_per_campo, tools)
        if errori_registro:
            return error_envelope("; ".join(errori_registro), 422)
        errori_tipo = valida_passi_per_tipo(body.impostazioni, tools)
        if errori_tipo:
            return _errori_body(errori_tipo, ["impostazioni", "passi_per_tipo"])
        try:
            repository.salva(body.impostazioni, body.revisione, body.sigla)
        except ConflictError:
            return _conflict(repository, tools)
        return _stato_attuale(repository, tools)


def _register_tipi_route(router: APIRouter, tools: dict[str, Tool]) -> None:
    @router.get("/tipi")
    def tipi() -> dict[str, Any]:
        per_tipo: dict[str, list[dict[str, str]]] = {t: [] for t in TIPI_DATO}
        senza_tipo: list[dict[str, str]] = []
        for tool in tools.values():
            for nome, schema_campo in campi_numerici(tool):
                voce = {
                    "strumento": tool.name, "campo": nome,
                    "simbolo": schema_campo.get("symbol", ""), "etichetta": schema_campo.get("description", ""),
                    "unita": schema_campo.get("unit", ""),
                }
                tipo = tipo_dato(nome, schema_campo)
                (per_tipo[tipo] if tipo is not None else senza_tipo).append(voce)
        return {
            "tipi": [
                {"tipo": t, "etichetta": _ETICHETTE_TIPO[t], "unita": _unita_del_tipo(t), "campi": per_tipo[t]}
                for t in TIPI_DATO
            ],
            "senza_tipo": senza_tipo,
        }


def _register_passi_route(router: APIRouter, repository: ImpostazioniRepository, tools: dict[str, Tool]) -> None:
    @router.get("/passi")
    def passi(strumento: str | None = None) -> Any:
        if not strumento:
            return _errori_body(("Indicare lo strumento",), ["query", "strumento"])
        tool = tools.get(strumento)
        if tool is None:
            return _unknown_tool(strumento)
        valori = repository.leggi().valori
        risultato: dict[str, Any] = {}
        for nome, schema_campo in campi_numerici(tool):
            tipo = tipo_dato(nome, schema_campo)
            try:
                proposto = passo_proposto(valori, strumento, nome, schema_campo, tipo)
            except ValueError as errore:
                risultato[nome] = {"passo": None, "origine": None, "tipo": tipo, "errore": str(errore)}
                continue
            risultato[nome] = {"passo": proposto.passo, "origine": proposto.origine, "tipo": proposto.tipo}
        return {
            "strumento": strumento,
            "obiettivo_sfruttamento": valori.obiettivo_sfruttamento,
            "obiettivo_su_verifiche_minimo": valori.obiettivo_su_verifiche_minimo,
            "passi": risultato,
        }


def _stato_attuale(repository: ImpostazioniRepository, tools: dict[str, Tool]) -> dict[str, Any]:
    salvate = repository.leggi()
    avvisi = list(_avvisi_lettura(repository))
    avvisi.extend(_avvisi_eccezioni_svanite(salvate.valori, tools))
    return {
        "ok": True,
        "impostazioni": salvate.valori.model_dump(mode="json"),
        "revisione": salvate.revisione,
        "sigla": salvate.sigla,
        "aggiornato_il": salvate.aggiornato_il,
        "fabbrica": FABBRICA.model_dump(mode="json"),
        "avvisi": avvisi,
    }


def _avvisi_lettura(repository: ImpostazioniRepository) -> tuple[str, ...]:
    _, avvisi = repository.leggi_con_avvisi()
    return avvisi


def _avvisi_eccezioni_svanite(valori: Impostazioni, tools: dict[str, Tool]) -> tuple[str, ...]:
    avvisi = []
    for messaggio in valida_eccezioni(valori.passi_per_campo, tools):
        avvisi.append(f"Eccezione ignorata: {messaggio}")
    return tuple(avvisi)


def _unita_del_tipo(tipo: str) -> str:
    if tipo == "lunghezza_m":
        return "m"
    if tipo == "lunghezza_cm":
        return "cm"
    if tipo == "intero":
        return ""
    return "mm"


class _PutBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    impostazioni: Impostazioni
    revisione: int = Field(ge=0)
    sigla: str = Field(min_length=1, max_length=MAX_SIGLA)


async def _parse_body(request: Request) -> _PutBody | JSONResponse:
    try:
        raw = await request.json()
    except ValueError:
        return error_envelope("Corpo della richiesta non è un JSON valido.", 400)
    if not isinstance(raw, dict):
        return error_envelope("Il corpo della richiesta deve essere un oggetto JSON.", 400)
    try:
        return _PutBody.model_validate(raw)
    except ValidationError as error:
        found = error.errors()
        messages = [messaggio_errore_it(e) for e in found]
        return JSONResponse(
            {
                "ok": False, "data": None, "checks": [], "warnings": [], "errors": messages,
                "error_details": [
                    {"loc": _loc_con_tipo(e, m), "message": m} for e, m in zip(found, messages, strict=True)
                ],
                "inputs_echo": {},
            },
            status_code=422,
        )


def _loc_con_tipo(errore: dict, messaggio: str) -> list:
    """`passi_per_tipo`'s own `field_validator` raises once for the WHOLE dict (pydantic has no
    per-key loc for a dict-level validator): the tipo it is actually about only shows up in the
    message text ("il passo di copriferro ..."). Recovering it here keeps §26.10's promise that a
    `passi_per_tipo` 422 points at the specific tipo, not just the field."""
    loc = list(errore["loc"])
    if loc[-1:] == ["passi_per_tipo"]:
        for tipo in TIPI_DATO:
            if f"di {tipo} " in messaggio or f" {tipo} " in messaggio:
                return [*loc, tipo]
    return loc


def _conflict(repository: ImpostazioniRepository, tools: dict[str, Tool]) -> JSONResponse:
    attuale = _stato_attuale(repository, tools)
    salvate = repository.leggi()
    body = {
        "ok": False, "data": None, "checks": [], "warnings": [],
        "errors": [
            (
                f"Le impostazioni sono state modificate nel frattempo (revisione {salvate.revisione}, "
                f"sigla {salvate.sigla}): ricaricare e riprovare"
            )
        ],
        "inputs_echo": {}, "attuale": attuale,
    }
    return JSONResponse(content=body, status_code=409)


def _unknown_tool(name: str) -> JSONResponse:
    return error_envelope(f"Strumento sconosciuto: {name}", 404)


def _errori_body(messaggi: tuple[str, ...], loc: list[str]) -> JSONResponse:
    body = {
        "ok": False, "data": None, "checks": [], "warnings": [], "errors": list(messaggi),
        "error_details": [{"loc": loc, "message": m} for m in messaggi], "inputs_echo": {},
    }
    return JSONResponse(content=body, status_code=422)
