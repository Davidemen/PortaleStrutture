"""`GET /api/progetti/{id}/stato` (WORKBENCH_SPEC.md §25.3): "da ricalcolare" propagated along the
usage chain, "provvisorio" per decisions 21-22. `routes/progetti.py` is already 358 lines, hence a
router of its own, wired in `web/app.py` next to it."""
import logging
from typing import Any

from fastapi import APIRouter

from strutture.shared.divergences.loader import load_register
from strutture.shared.divergences.models import Divergence
from strutture.shared.divergences.riepilogo import riepilogo_per_strumento
from strutture.shared.stato_progetto.conteggi import conta
from strutture.shared.stato_progetto.origini import LimiteRicalcoliRaggiunto, stato_origini
from strutture.shared.stato_progetto.propagazione import Arco, OwnState, cicli, propaga
from strutture.shared.stato_progetto.provvisorio import stato_provvisorio
from strutture.shared.stato_progetto.valutazione import valore_attuale_a_percorso
from strutture.shared.tool import Tool
from strutture.storage.interfaces import NotFoundError, ProjectRepository, SignoffRepository

from ..envelope import error_envelope

logger = logging.getLogger(__name__)
MAX_RICALCOLI_ORIGINI = 50


def build_progetti_stato_router(
    progetti: ProjectRepository,
    tools: dict[str, Tool],
    signoffs: SignoffRepository,
    register: tuple[Divergence, ...] | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/progetti/{progetto_id}/stato")
    def stato(progetto_id: str) -> Any:
        try:
            progetti.get_progetto(progetto_id)
            elementi = progetti.list_elementi(progetto_id)
        except NotFoundError:
            return _not_found_progetto(progetto_id)
        return _calcola(elementi, progetti, tools, signoffs, register)

    return router


def _per_provvisorio(voce: dict | None) -> dict | None:
    """`riepilogo_per_strumento`'s `da_confermare`/`ramo_nessuno` count EVERY divergence, doubts
    ("da_verificare") included (GET /api/divergences/riepilogo needs that, unchanged); `stato_
    provvisorio` must NOT (§25.2: a doubt never makes an element provisional). Its own `correzioni`/
    `correzioni_ramo_nessuno` sub-dicts already exclude them -- this just renames them back onto the
    flat shape `stato_provvisorio` expects."""
    if voce is None:
        return None
    return {
        "da_confermare": voce["correzioni"]["da_confermare"],
        "approvato": voce["correzioni"]["approvato"],
        "respinto": voce["correzioni"]["respinto"],
        "ramo_nessuno": voce["correzioni_ramo_nessuno"],
        "da_verificare": voce["da_verificare"],
    }


def _calcola(
    elementi: tuple, progetti: ProjectRepository, tools: dict[str, Tool],
    signoffs: SignoffRepository, register: tuple[Divergence, ...] | None,
) -> dict[str, Any]:
    tutte_le_divergenze = register if register is not None else load_register()
    riepilogo = riepilogo_per_strumento(tutte_le_divergenze, signoffs)
    contesto = _ContestoValutazione(progetti, tools, riepilogo)

    archi = {
        elemento.id: _archi_di(elemento) for elemento in elementi
    }
    ids_ciclo = cicli(archi)

    voci: dict[str, dict[str, Any]] = {}
    for elemento in elementi:
        origini, provvisorio_proprio = contesto.stato_proprio_completo(elemento)
        propagato = propaga(elemento.id, archi, contesto.own_state, ids_ciclo)
        voci[elemento.id] = _voce(elemento, origini, provvisorio_proprio, propagato)

    conteggi = conta((e.stato for e in elementi), voci.values())
    return {"elementi": voci, "conteggi": conteggi.__dict__}


def _archi_di(elemento: Any) -> tuple[Arco, ...]:
    collegamenti = _collegamenti_di(elemento)
    return tuple(
        Arco(item["elemento_id"], item.get("strumento", ""), item.get("chiave", ""))
        for item in collegamenti if isinstance(item, dict) and item.get("elemento_id")
    )


def _voce(elemento: Any, origini, provvisorio_proprio, propagato) -> dict[str, Any]:
    motivi = [
        {"chiave": m.chiave, "strumento": m.strumento, "elemento_id": m.elemento_id, "causa": m.causa,
         "valore_salvato": m.valore_salvato, "valore_attuale": m.valore_attuale, **({"messaggio": m.messaggio} if m.messaggio else {})}
        for m in origini.motivi
    ] + [
        {"chiave": "", "strumento": m.strumento, "elemento_id": m.elemento_id, "causa": m.causa,
         "valore_salvato": None, "valore_attuale": None, **({"messaggio": m.messaggio} if m.messaggio else {})}
        for m in propagato.motivi_ricalcolo
    ]
    return {
        "da_ricalcolare": origini.da_ricalcolare or propagato.da_ricalcolare_per_origine,
        "motivi": motivi,
        "provvisorio": provvisorio_proprio.provvisorio,
        "provvisorio_origine": propagato.provvisorio_origine,
        "motivi_origine": propagato.motivi_provvisorio,
        "correzioni": provvisorio_proprio.correzioni.__dict__,
    }


class _ContestoValutazione:
    """Per-request evaluation: memoises each element's own state (§25.3, "computed at most once per
    elemento_id per request") and caps provider runs at `MAX_RICALCOLI_ORIGINI`."""

    def __init__(self, progetti: ProjectRepository, tools: dict[str, Tool], riepilogo: dict) -> None:
        self._progetti = progetti
        self._tools = tools
        self._riepilogo = riepilogo
        self._cache_own_state: dict[str, OwnState] = {}
        self._cache_completo: dict[str, tuple] = {}
        self._ricalcoli_usati = 0

    def own_state(self, elemento_id: str) -> OwnState:
        if elemento_id in self._cache_own_state:
            return self._cache_own_state[elemento_id]
        elemento = self._get_elemento(elemento_id)
        if elemento is None:
            risultato = OwnState(da_ricalcolare=False, messaggio="", provvisorio=False, excel=False)
        else:
            origini, provvisorio = self.stato_proprio_completo(elemento)
            messaggio = origini.motivi[0].messaggio if origini.motivi else ""
            risultato = OwnState(
                da_ricalcolare=origini.da_ricalcolare, messaggio=messaggio,
                provvisorio=provvisorio.provvisorio, excel=elemento.modalita == "excel",
            )
        self._cache_own_state[elemento_id] = risultato
        return risultato

    def stato_proprio_completo(self, elemento: Any) -> tuple:
        if elemento.id in self._cache_completo:
            return self._cache_completo[elemento.id]
        origini = stato_origini(_collegamenti_di(elemento), self._get_elemento, self._valore_attuale)
        provvisorio = stato_provvisorio(_per_provvisorio(self._riepilogo.get(elemento.strumento)), elemento.modalita)
        risultato = (origini, provvisorio)
        self._cache_completo[elemento.id] = risultato
        return risultato

    def _get_elemento(self, elemento_id: str) -> Any | None:
        try:
            elemento = self._progetti.get_elemento(elemento_id)
        except NotFoundError:
            return None
        return None if elemento.eliminato else elemento

    def _valore_attuale(self, elemento: Any, percorso: str, ingresso: bool) -> Any:
        if self._ricalcoli_usati >= MAX_RICALCOLI_ORIGINI:
            raise LimiteRicalcoliRaggiunto()
        self._ricalcoli_usati += 1
        return valore_attuale_a_percorso(elemento, percorso, ingresso, self._tools)


def _collegamenti_di(elemento: Any) -> list[dict]:
    return elemento.provenienza.get("collegamenti", []) if isinstance(elemento.provenienza, dict) else []


def _not_found_progetto(progetto_id: str):
    return error_envelope(f"Progetto sconosciuto: {progetto_id}", 404)
