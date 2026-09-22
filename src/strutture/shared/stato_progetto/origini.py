"""§25.1: an element's OWN "da ricalcolare" state, from its saved `provenienza.collegamenti` items.

Pure: the route supplies `get_elemento` (may reach across projects) and `valore_attuale_fornitore`
(runs the provider's tool with its current stored inputs and reads the value at `percorso`)."""
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

Causa = Literal["valore_cambiato", "origine_eliminata", "origine_non_calcolabile", "controllo_rinviato"]
TOLLERANZA_RELATIVA = 1e-9
MOTIVO_ORIGINE_ELIMINATA = "L'origine è stata eliminata"
MOTIVO_ORIGINE_NON_CALCOLABILE = "L'origine non è più calcolabile con i suoi dati salvati"
MOTIVO_CONTROLLO_RINVIATO = "Troppe origini da ricalcolare in questa richiesta: controllo rinviato"


class LimiteRicalcoliRaggiunto(Exception):
    """Raised by `valore_attuale_fornitore` when the request's `MAX_RICALCOLI_ORIGINI` provider runs
    are exhausted (§25.3): the item is reported, never marked, so it never hides a real problem."""


@dataclass(frozen=True)
class Motivo:
    chiave: str
    strumento: str
    elemento_id: str
    causa: Causa
    valore_salvato: Any
    valore_attuale: Any
    messaggio: str = ""


@dataclass(frozen=True)
class StatoOrigini:
    da_ricalcolare: bool
    motivi: tuple[Motivo, ...]


def stato_origini(
    collegamenti: Sequence[Mapping[str, Any]],
    get_elemento: Callable[[str], Any | None],
    valore_attuale_fornitore: Callable[[Any, str, bool], Any],
) -> StatoOrigini:
    motivi = tuple(
        motivo for item in collegamenti
        if (motivo := _motivo_di(item, get_elemento, valore_attuale_fornitore)) is not None
    )
    return StatoOrigini(da_ricalcolare=any(m.causa != "controllo_rinviato" for m in motivi), motivi=motivi)


def _motivo_di(item: Mapping[str, Any], get_elemento, valore_attuale_fornitore) -> Motivo | None:
    elemento_id = item.get("elemento_id")
    if not elemento_id:
        return None  # "origine non salvata": never marks, never propagates (§25.1)
    fornitore = get_elemento(elemento_id)
    if fornitore is None:
        return Motivo(item["chiave"], item["strumento"], elemento_id, "origine_eliminata",
                       item.get("valore"), None, MOTIVO_ORIGINE_ELIMINATA)
    try:
        valore_attuale = valore_attuale_fornitore(fornitore, item["percorso"], bool(item.get("ingresso", False)))
    except LimiteRicalcoliRaggiunto:
        return Motivo(item["chiave"], item["strumento"], elemento_id, "controllo_rinviato",
                       item.get("valore"), None, MOTIVO_CONTROLLO_RINVIATO)
    except Exception:  # noqa: BLE001 - any failure of the provider's own run means "non calcolabile"
        return Motivo(item["chiave"], item["strumento"], elemento_id, "origine_non_calcolabile",
                       item.get("valore"), None, MOTIVO_ORIGINE_NON_CALCOLABILE)
    if valore_attuale is None or _diverso(item.get("valore"), valore_attuale):
        return Motivo(item["chiave"], item["strumento"], elemento_id, "valore_cambiato",
                       item.get("valore"), valore_attuale, _messaggio(item, valore_attuale))
    return None


def _diverso(salvato: Any, attuale: Any) -> bool:
    if _numero(salvato) and _numero(attuale):
        if salvato == 0:
            return abs(attuale) > TOLLERANZA_RELATIVA
        return abs((attuale - salvato) / salvato) > TOLLERANZA_RELATIVA
    return salvato != attuale


def _numero(valore: Any) -> bool:
    return isinstance(valore, int | float) and not isinstance(valore, bool)


def _messaggio(item: Mapping[str, Any], valore_attuale: Any) -> str:
    return f"{item['chiave']}: {item.get('valore')} → {valore_attuale}"
