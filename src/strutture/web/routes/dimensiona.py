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
    N_CAMPIONI,
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
from strutture.shared.divergences.riepilogo import riepilogo_per_strumento
from strutture.shared.tool import Tool, execute
from strutture.storage.interfaces import SignoffRepository

from ..envelope import error_envelope, internal_error_envelope
from ..errori_it import messaggio_errore_it

logger = logging.getLogger(__name__)

MAX_VALUTAZIONI = 80
TEMPO_MAX_S = 10.0
MAX_RICERCHE_CONTEMPORANEE = 2
_TROPPE_RICERCHE_IT = "Un'altra ricerca è in corso: riprovare fra qualche secondo."
_MOTIVO_OBIETTIVO_SU_MINIMI = (
    "Obiettivo applicato anche a eventuali limiti massimi di dettaglio: controllare"
)
_MOTIVO_EXCEL = "Valore trovato riproducendo il foglio Excel, errori inclusi"


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
        errore = _valida_intervallo(campo_schema, corpo.da, corpo.a)
        if errore is not None:
            return errore
        base_report, errore = _valida_inputs_base(tool, corpo.inputs)
        if errore is not None:
            return errore
        stato = _stato_dimensiona(request)
        if not stato.semaforo.acquire(blocking=False):
            return error_envelope(_TROPPE_RICERCHE_IT, 429)
        try:
            return await run_in_threadpool(
                _esegui_dimensiona, tool, corpo, campo_schema, base_report, signoffs, impostazioni, register, stato,
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
        campo_schema, errore = _valida_campo(tool, corpo.campo)
        if errore is not None:
            return errore
        errore = _valida_intervallo(campo_schema, corpo.da, corpo.a)
        if errore is not None:
            return errore
        _, errore = _valida_inputs_base(tool, corpo.inputs)
        if errore is not None:
            return errore
        # §24.1: a search-worthy tool that is register-approved never studies its Excel branch by
        # accident (same forcing `_esegui_dimensiona` applies for /dimensiona).
        modalita, correzioni = _stato_registro(tool, corpo.inputs, signoffs, register)
        inputs = _inputs_per_modalita(tool, corpo.inputs, modalita)
        stato = _stato_dimensiona(request)
        if not stato.semaforo.acquire(blocking=False):
            return error_envelope(_TROPPE_RICERCHE_IT, 429)
        try:
            serie = await run_in_threadpool(
                calcola_serie, tool, inputs, corpo.campo, corpo.da, corpo.a, corpo.punti,
                tempo_max_s=stato.tempo_max_s,
            )
        except Exception:
            logger.exception("unexpected error in sensitivity study for %s", name)
            return internal_error_envelope()
        finally:
            stato.semaforo.release()
        return {
            "ok": True, "campo": corpo.campo, "valori": serie.valori,
            "verifiche": [v.__dict__ for v in serie.verifiche],
            "errori": serie.errori, "verifiche_solo_esito": serie.verifiche_solo_esito,
            "modalita": modalita, "correzioni": correzioni, "completa": serie.completa,
        }


def _stato_dimensiona(request: Request) -> StatoDimensiona:
    return getattr(request.app.state, "dimensiona", None) or StatoDimensiona()


def _inputs_per_modalita(tool: Tool, inputs: dict[str, Any], modalita: str) -> dict[str, Any]:
    if modalita == "standard" and "legacy_compat" in tool.input_model.model_fields:
        return {**inputs, "legacy_compat": False}
    return inputs


def _esegui_dimensiona(
    tool: Tool, corpo: CorpoDimensiona, campo_schema: dict[str, Any], base_report: Any, signoffs: SignoffRepository,
    impostazioni: LettoreImpostazioni | None, register: tuple[Divergence, ...] | None, stato: StatoDimensiona,
) -> Any:
    inizio = time.monotonic()
    modalita, correzioni = _stato_registro(tool, corpo.inputs, signoffs, register)
    inputs = _inputs_per_modalita(tool, corpo.inputs, modalita)
    intero = campo_schema.get("type") == "integer"
    try:
        griglia = costruisci_griglia(corpo.da, corpo.a, corpo.passo, intero=intero)
    except GrigliaError as errore:
        return _errore_body(str(errore), "passo" if "passo" in str(errore).lower() else "da", 422)
    obiettivo_su_minimi = impostazioni.obiettivo_su_verifiche_minimo(tool.name) if impostazioni else False
    riporti = valutazioni_iniziali(tool, inputs, corpo.campo, griglia)
    orientamenti = impara_da_riporti(riporti)
    # §23.3 point 2: "nuovi avvisi" are measured against the ENGINEER'S OWN submitted `inputs` at
    # the request's own mode (`base_report`, already computed once by `_valida_inputs_base` -- one
    # execute() reused, not a second one), not against whatever the grid's first sample happens to
    # be, which may not even be admissible.
    avvisi_base = tuple(base_report.warnings) if base_report.ok else ()
    valuta, cache = costruisci_valuta(tool, inputs, corpo.campo, riporti, orientamenti, corpo.obiettivo, obiettivo_su_minimi, avvisi_base)
    # §23.3 point 6: `TEMPO_MAX_S` covers the WHOLE search, not just `cerca()`'s own clock -- the
    # `N_CAMPIONI` initial samples above already spent real wall time that must count against it,
    # or a slow tool's initial sampling alone could exceed the advertised budget unnoticed.
    tempo_restante = max(stato.tempo_max_s - (time.monotonic() - inizio), 0.0)
    risultato = cerca(griglia, valuta, corpo.verso, max_valutazioni=stato.max_valutazioni, tempo_max_s=tempo_restante)
    report, esito = esito_alla_risposta(
        risultato.valore, tool, inputs, corpo.campo, cache, orientamenti, corpo.obiettivo, obiettivo_su_minimi,
    )
    affidabile, motivi = _affidabilita_finale(risultato, esito, modalita, corpo.obiettivo, obiettivo_su_minimi, griglia)
    return _risposta_dimensiona(
        corpo, risultato, report, esito, modalita, correzioni, obiettivo_su_minimi, affidabile, motivi,
        time.monotonic() - inizio,
    )


def _affidabilita_finale(
    risultato: Any, esito: Any, modalita: str, obiettivo: float, obiettivo_su_minimi: bool, griglia: tuple,
) -> tuple[bool, tuple[str, ...]]:
    """Composes the response's own `affidabile`/`motivi` from `risultato`'s (the search algorithm's
    own reliability) plus three more §23.2/§23.3/§24.1 rules the search itself knows nothing
    about: the objective silently reaching "inverso" checks, an Excel-mode result, and an
    orientation that held on the initial samples but was contradicted later."""
    motivi = list(risultato.motivi)
    affidabile = risultato.affidabile
    if not obiettivo_su_minimi and obiettivo < 1 and _MOTIVO_OBIETTIVO_SU_MINIMI not in motivi:
        affidabile = False
        motivi.append(_MOTIVO_OBIETTIVO_SU_MINIMI)
    if modalita == "excel":
        affidabile = False
        motivi.append(_MOTIVO_EXCEL)
    if esito is not None:
        for nome in esito.incoerenze:
            affidabile = False
            motivi.append(f"Orientamento della verifica {nome} incoerente")
    # §23.3 point 5: "always declared, never hidden" -- sampling cannot see windows narrower than
    # one sampling interval, so whenever the not-monotone path was taken the response says how much
    # of the grid the initial probing actually covered.
    if any("non è monotono" in m for m in risultato.motivi):
        motivi.append(f"Campionamento: {min(N_CAMPIONI, len(griglia))} punti su {len(griglia)} valori")
    return affidabile, tuple(motivi)


def _risposta_dimensiona(corpo, risultato, report, esito, modalita, correzioni, obiettivo_su_minimi, affidabile, motivi, durata):
    governante = {"nome": esito.governante[0], "eta": esito.governante[1]} if esito and esito.governante else None
    return {
        "ok": True, "campo": corpo.campo, "verso": risultato.verso, "esito": risultato.esito,
        "valore": float(risultato.valore) if risultato.valore is not None else None,
        "affidabile": affidabile, "motivi": motivi, "governante": governante,
        "verifiche_solo_esito": esito.solo_esito if esito else (),
        "verifiche_senza_obiettivo": esito.senza_obiettivo if esito else (),
        "campioni": [
            {"valore": float(c.valore), "esito": c.esito, "eta_max": c.eta_max, "messaggio": c.messaggio,
             "avvisi_nuovi": c.avvisi_nuovi}
            for c in risultato.campioni
        ],
        "valutazioni": risultato.valutazioni, "durata_s": durata, "modalita": modalita, "correzioni": correzioni,
        "obiettivo": corpo.obiettivo, "passo": corpo.passo, "obiettivo_su_minimi": obiettivo_su_minimi, "report": report,
    }


def _stato_registro(
    tool: Tool, inputs: dict[str, Any], signoffs: SignoffRepository, register: tuple[Divergence, ...] | None,
) -> tuple[str, dict[str, int]]:
    """`modalita`/`correzioni` read the way §25.2 reads them (`riepilogo_per_strumento`'s own
    `correzioni` sub-dict, shared with `routes/progetti_stato.py`): an approved tool (register
    entries present, none pending/rejected) never runs in Excel mode even if the request asked for
    it. `ramo_nessuno`'s subset is not this route's concern (Excel-mode reproduction, §25.2's own
    domain) -- `correzioni`'s unfiltered-by-ramo counts are what "approvato" already meant here."""
    entries = register if register is not None else load_register()
    voce = riepilogo_per_strumento(entries, signoffs).get(tool.name)
    counts = (
        {"da_confermare": voce["correzioni"]["da_confermare"], "respinto": voce["correzioni"]["respinto"]}
        if voce is not None else {"da_confermare": 0, "respinto": 0}
    )
    approvato = voce is not None and counts["da_confermare"] == 0 and counts["respinto"] == 0
    legacy_richiesto = bool(inputs.get("legacy_compat")) and "legacy_compat" in tool.input_model.model_fields
    modalita = "excel" if (legacy_richiesto and not approvato) else "standard"
    return modalita, counts


def _valida_campo(tool: Tool, campo: str) -> tuple[dict[str, Any], None] | tuple[None, Any]:
    schema = tool.input_model.model_json_schema()
    proprieta = schema.get("properties", {})
    info = proprieta.get(campo)
    if info is None:
        return None, _errore_body(f"Il campo {campo} non è numerico", "campo", 422)
    risolto = _risolvi_schema_campo(info)
    if campo == "legacy_compat" or risolto.get("type") not in ("number", "integer") or "enum" in risolto:
        return None, _errore_body(f"Il campo {campo} non è numerico", "campo", 422)
    return risolto, None


def _risolvi_schema_campo(info: dict[str, Any]) -> dict[str, Any]:
    """An optional numeric field (`float | None`) has no top-level `type`: pydantic puts the real
    numeric branch (with `type`/`gt`/`le`/...) inside `anyOf`, alongside a bare `{"type": "null"}`.
    `unit`/`symbol`/... stay at the top level either way -- merge the numeric branch UNDER them so
    a field's own metadata still wins if it is ever repeated in both places."""
    if "type" in info or "anyOf" not in info:
        return info
    for ramo in info["anyOf"]:
        if isinstance(ramo, dict) and ramo.get("type") in ("number", "integer"):
            return {**ramo, **{k: v for k, v in info.items() if k != "anyOf"}}
    return info


def _valida_intervallo(campo_schema: dict[str, Any], da: float, a: float) -> JSONResponse | None:
    """§23.4/§23.3 point 7/§24.1: `da` must be less than `a` (`/dimensiona`'s own `costruisci_
    griglia` already checks this too, redundantly but harmlessly; `/sensibilita`'s `punti_
    equispaziati` does not, so this is the only place it is actually enforced for that route), and
    both outside the field's own schema limits (exclusive `gt`/`lt`, inclusive `ge`/`le`) is a 422
    naming which of the two, before any tool ever runs."""
    if da >= a:
        return _errore_body("Il valore «da» deve essere minore di «a»", "da", 422)
    for nome, valore in (("da", da), ("a", a)):
        errore = _fuori_limite(campo_schema, nome, valore)
        if errore is not None:
            return errore
    return None


def _fuori_limite(campo_schema: dict[str, Any], nome: str, valore: float) -> JSONResponse | None:
    if "exclusiveMinimum" in campo_schema and not valore > campo_schema["exclusiveMinimum"]:
        return _errore_body(f"Il valore «{nome}» deve essere maggiore di {campo_schema['exclusiveMinimum']}", nome, 422)
    if "minimum" in campo_schema and not valore >= campo_schema["minimum"]:
        return _errore_body(f"Il valore «{nome}» deve essere almeno {campo_schema['minimum']}", nome, 422)
    if "exclusiveMaximum" in campo_schema and not valore < campo_schema["exclusiveMaximum"]:
        return _errore_body(f"Il valore «{nome}» deve essere minore di {campo_schema['exclusiveMaximum']}", nome, 422)
    if "maximum" in campo_schema and not valore <= campo_schema["maximum"]:
        return _errore_body(f"Il valore «{nome}» deve essere al massimo {campo_schema['maximum']}", nome, 422)
    return None


def _valida_inputs_base(tool: Tool, inputs: dict[str, Any]) -> tuple[Any, None] | tuple[None, JSONResponse]:
    """§23.3 point 7/§24.1: the `inputs` the engineer actually submitted must themselves be valid
    BEFORE any grid point ever runs -- a bad base input (out of range, wrong type, missing) is
    rejected with the tool's own 422, the same it would give through `/api/tools/{name}` itself.
    The successful `Report` is returned too so the caller can reuse it (its `warnings` are the
    "avvisi_base" §23.3 point 2 needs) instead of running `execute` on the same inputs twice."""
    report = execute(tool, inputs)
    if not report.ok:
        messaggi = list(report.errors) or ["I dati non sono validi"]
        body = {
            "ok": False, "data": None, "checks": [], "warnings": [], "errors": messaggi,
            "error_details": [d.model_dump(mode="json") for d in report.error_details] or [{"loc": ["inputs"], "message": m} for m in messaggi],
            "inputs_echo": {},
        }
        return None, JSONResponse(content=body, status_code=422)
    return report, None


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
        return None, _errore_body(messaggio_errore_it(primo), loc, 422)


def _errore_body(messaggio: str, loc: str, status_code: int) -> JSONResponse:
    body = {"ok": False, "data": None, "checks": [], "warnings": [], "errors": [messaggio],
            "error_details": [{"loc": [loc], "message": messaggio}], "inputs_echo": {}}
    return JSONResponse(content=body, status_code=status_code)


def _sconosciuto(name: str):
    return error_envelope(f"Strumento sconosciuto: {name}", 404)
