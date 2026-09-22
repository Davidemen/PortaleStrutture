"""`/api/tools/{name}/dimensiona` and `/api/tools/{name}/sensibilita` (WORKBENCH_SPEC §23-24). Kept
out of `routes/tools.py` (rule: keep that router small)."""
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from strutture.shared.dimensiona.esecuzione import (
    costruisci_valuta,
    esito_alla_risposta,
    impara_da_riporti,
    valutazioni_iniziali,
)
from strutture.shared.dimensiona.griglia import GrigliaError, costruisci_griglia
from strutture.shared.dimensiona.modelli import CorpoDimensiona, CorpoSensibilita
from strutture.shared.dimensiona.ricerca import cerca
from strutture.shared.dimensiona.serie import calcola_serie
from strutture.shared.divergences import Divergence, load_register
from strutture.shared.tool import Tool
from strutture.storage.interfaces import SignoffRepository

from ..envelope import error_envelope, internal_error_envelope

logger = logging.getLogger(__name__)

MAX_VALUTAZIONI = 80
TEMPO_MAX_S = 10.0
MAX_RICERCHE_CONTEMPORANEE = 2
_TROPPE_RICERCHE_IT = "Un'altra ricerca è in corso: riprovare fra qualche secondo."


class LettoreImpostazioni(Protocol):
    """§26 hook, not built this wave: resolves `obiettivo_su_verifiche_minimo` for a tool. `None`
    (the default) keeps the factory value (`false`, §23.7 decision 19-bis)."""

    def obiettivo_su_verifiche_minimo(self, tool: str) -> bool: ...


@dataclass
class StatoDimensiona:
    """Injectable via `app.state.dimensiona` (tests replace the clock/limits so nothing waits 10s)."""

    semaforo: threading.BoundedSemaphore = field(default_factory=lambda: threading.BoundedSemaphore(MAX_RICERCHE_CONTEMPORANEE))
    max_valutazioni: int = MAX_VALUTAZIONI
    tempo_max_s: float = TEMPO_MAX_S


def build_dimensiona_router(
    tools: dict[str, Tool], signoffs: SignoffRepository, impostazioni: LettoreImpostazioni | None = None,
    register: tuple[Divergence, ...] | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/tools")
    _register_dimensiona_route(router, tools, signoffs, impostazioni, register)
    _register_sensibilita_route(router, tools, signoffs, register)
    return router


def _register_dimensiona_route(
    router: APIRouter, tools: dict[str, Tool], signoffs: SignoffRepository,
    impostazioni: LettoreImpostazioni | None, register: tuple[Divergence, ...] | None,
) -> None:
    @router.post("/{name}/dimensiona")
    async def dimensiona(name: str, request: Request) -> Any:
        tool = tools.get(name)
        if tool is None:
            return _sconosciuto(name)
        corpo, errore = await _leggi_corpo(request, CorpoDimensiona)
        if errore is not None:
            return errore
        campo_schema, errore = _valida_campo(tool, corpo.campo)
        if errore is not None:
            return errore
        stato = getattr(request.app.state, "dimensiona", None) or StatoDimensiona()
        if not stato.semaforo.acquire(blocking=False):
            return error_envelope(_TROPPE_RICERCHE_IT, 429)
        try:
            return await run_in_threadpool(
                _esegui_dimensiona, tool, corpo, campo_schema, signoffs, impostazioni, register, stato,
            )
        except Exception:
            logger.exception("unexpected error sizing tool %s", name)
            return internal_error_envelope()
        finally:
            stato.semaforo.release()


def _register_sensibilita_route(
    router: APIRouter, tools: dict[str, Tool], signoffs: SignoffRepository, register: tuple[Divergence, ...] | None,
) -> None:
    @router.post("/{name}/sensibilita")
    async def sensibilita(name: str, request: Request) -> Any:
        tool = tools.get(name)
        if tool is None:
            return _sconosciuto(name)
        corpo, errore = await _leggi_corpo(request, CorpoSensibilita)
        if errore is not None:
            return errore
        _, errore = _valida_campo(tool, corpo.campo)
        if errore is not None:
            return errore
        try:
            serie = await run_in_threadpool(calcola_serie, tool, corpo.inputs, corpo.campo, corpo.da, corpo.a, corpo.punti)
        except Exception:
            logger.exception("unexpected error in sensitivity study for %s", name)
            return internal_error_envelope()
        modalita, correzioni = _stato_registro(tool, corpo.inputs, signoffs, register)
        return {
            "ok": True, "campo": corpo.campo, "valori": serie.valori,
            "verifiche": [v.__dict__ for v in serie.verifiche],
            "errori": serie.errori, "verifiche_solo_esito": serie.verifiche_solo_esito,
            "modalita": modalita, "correzioni": correzioni, "completa": serie.completa,
        }


def _esegui_dimensiona(
    tool: Tool, corpo: CorpoDimensiona, campo_schema: dict[str, Any], signoffs: SignoffRepository,
    impostazioni: LettoreImpostazioni | None, register: tuple[Divergence, ...] | None, stato: StatoDimensiona,
) -> Any:
    inizio = time.monotonic()
    modalita, correzioni = _stato_registro(tool, corpo.inputs, signoffs, register)
    inputs = {**corpo.inputs, "legacy_compat": False} if modalita == "standard" and "legacy_compat" in tool.input_model.model_fields else corpo.inputs
    intero = campo_schema.get("type") == "integer"
    try:
        griglia = costruisci_griglia(corpo.da, corpo.a, corpo.passo, intero=intero)
    except GrigliaError as errore:
        return _errore_body(str(errore), "passo" if "passo" in str(errore).lower() else "da", 422)
    obiettivo_su_minimi = impostazioni.obiettivo_su_verifiche_minimo(tool.name) if impostazioni else False
    riporti = valutazioni_iniziali(tool, inputs, corpo.campo, griglia)
    orientamenti = impara_da_riporti(riporti)
    base = riporti.get(griglia[0], next(iter(riporti.values())))
    avvisi_base = tuple(base.get("warnings", ())) if base.get("ok") else ()
    valuta, cache = costruisci_valuta(tool, inputs, corpo.campo, riporti, orientamenti, corpo.obiettivo, obiettivo_su_minimi, avvisi_base)
    risultato = cerca(griglia, valuta, corpo.verso, max_valutazioni=stato.max_valutazioni, tempo_max_s=stato.tempo_max_s)
    report, esito = esito_alla_risposta(
        risultato.valore, tool, inputs, corpo.campo, cache, orientamenti, corpo.obiettivo, obiettivo_su_minimi,
    )
    return _risposta_dimensiona(corpo, risultato, report, esito, modalita, correzioni, obiettivo_su_minimi, time.monotonic() - inizio)


def _risposta_dimensiona(corpo, risultato, report, esito, modalita, correzioni, obiettivo_su_minimi, durata):
    governante = {"nome": esito.governante[0], "eta": esito.governante[1]} if esito and esito.governante else None
    return {
        "ok": True, "campo": corpo.campo, "verso": risultato.verso, "esito": risultato.esito,
        "valore": float(risultato.valore) if risultato.valore is not None else None,
        "affidabile": risultato.affidabile, "motivi": risultato.motivi, "governante": governante,
        "verifiche_solo_esito": esito.solo_esito if esito else (),
        "verifiche_senza_obiettivo": esito.senza_obiettivo if esito else (),
        "campioni": [
            {"valore": float(c.valore), "esito": c.esito, "eta_max": c.eta_max, "messaggio": c.messaggio,
             "avvisi_nuovi": (c.avviso_nuovo,) if c.avviso_nuovo else ()}
            for c in risultato.campioni
        ],
        "valutazioni": risultato.valutazioni, "durata_s": durata, "modalita": modalita, "correzioni": correzioni,
        "obiettivo": corpo.obiettivo, "passo": corpo.passo, "obiettivo_su_minimi": obiettivo_su_minimi, "report": report,
    }


def _stato_registro(
    tool: Tool, inputs: dict[str, Any], signoffs: SignoffRepository, register: tuple[Divergence, ...] | None,
) -> tuple[str, dict[str, int]]:
    """`modalita`/`correzioni` read the way §25.2 reads them: an approved tool (register entries
    present, none pending/rejected) never runs in Excel mode even if the request asked for it."""
    entries = register if register is not None else load_register()
    per_tool = [d for d in entries if tool.name in d.strumenti]
    stati = [signoffs.get(d.id).stato for d in per_tool]
    counts = {"da_confermare": stati.count("da_confermare"), "respinto": stati.count("respinto")}
    approvato = bool(per_tool) and counts["da_confermare"] == 0 and counts["respinto"] == 0
    legacy_richiesto = bool(inputs.get("legacy_compat")) and "legacy_compat" in tool.input_model.model_fields
    modalita = "excel" if (legacy_richiesto and not approvato) else "standard"
    return modalita, counts


def _valida_campo(tool: Tool, campo: str) -> tuple[dict[str, Any], None] | tuple[None, Any]:
    schema = tool.input_model.model_json_schema()
    proprieta = schema.get("properties", {})
    info = proprieta.get(campo)
    if campo == "legacy_compat" or info is None or info.get("type") not in ("number", "integer") or "enum" in info:
        return None, _errore_body(f"Il campo {campo} non è numerico", "campo", 422)
    return info, None


async def _leggi_corpo(request: Request, modello):
    try:
        raw = await request.json()
    except ValueError:
        return None, error_envelope("Corpo della richiesta non è un JSON valido.", 400)
    if not isinstance(raw, dict):
        return None, error_envelope("Il corpo della richiesta deve essere un oggetto JSON.", 400)
    try:
        return modello.model_validate(raw), None
    except ValidationError as errore:
        primo = errore.errors()[0]
        loc = ".".join(str(p) for p in primo["loc"]) or "corpo"
        return None, _errore_body(str(primo["msg"]).removeprefix("Value error, "), loc, 422)


def _errore_body(messaggio: str, loc: str, status_code: int) -> JSONResponse:
    body = {"ok": False, "data": None, "checks": [], "warnings": [], "errors": [messaggio],
            "error_details": [{"loc": [loc], "message": messaggio}], "inputs_echo": {}}
    return JSONResponse(content=body, status_code=status_code)


def _sconosciuto(name: str):
    return error_envelope(f"Strumento sconosciuto: {name}", 404)
