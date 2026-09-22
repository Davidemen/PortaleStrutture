"""Entry point of the search (WORKBENCH_SPEC §23.3): sample the grid, then dispatch to the matching
outcome — bisection for a single admissibility change, or the `esiti` fallbacks otherwise."""
import time
from decimal import Decimal
from typing import Literal

from .bisezione import bisezione
from .campioni import Campione, Risultato, Sessione, Valuta, cat, interrotta
from .esecuzione import N_CAMPIONI
from .esiti import nessun_valore, non_monotona, tutto_ammissibile
from .griglia import indici_campionamento

VersoRichiesto = Literal["auto", "minimo", "massimo"]


def cerca(
    griglia: tuple[Decimal, ...], valuta: Valuta, verso_richiesto: VersoRichiesto,
    *, max_valutazioni: int = 80, tempo_max_s: float = 10.0,
) -> Risultato:
    sessione = Sessione(valuta, max_valutazioni, time.monotonic() + tempo_max_s)
    indici = indici_campionamento(len(griglia), N_CAMPIONI)
    campioni: list[Campione] = []
    for indice in indici:
        campione = sessione.prova(griglia[indice])
        if campione is None:
            return interrotta(campioni, verso_richiesto, sessione.valutazioni)
        campioni.append(campione)
    return _decidi(tuple(campioni), indici, griglia, verso_richiesto, sessione)


def _runs(cats: tuple[str, ...]) -> tuple[tuple[str, int, int], ...]:
    runs: list[tuple[str, int, int]] = []
    for i, c in enumerate(cats):
        if runs and runs[-1][0] == c:
            runs[-1] = (c, runs[-1][1], i)
        else:
            runs.append((c, i, i))
    return tuple(runs)


def _pattern(runs: tuple[tuple[str, int, int], ...]) -> tuple[str, bool, int, int] | None:
    """Exactly one boundary, its verso, and the campioni-list indices to bisect between. `limite`
    marks the "errore band next to admissible" case (§23.3 point 3, `limite_validita`)."""
    if len(runs) != 2:
        return None
    (cat0, _, e0), (cat1, s1, _) = runs
    if {cat0, cat1} == {"N", "A"}:
        return ("minimo" if cat0 == "N" else "massimo", False, e0, s1)
    if {cat0, cat1} == {"E", "A"}:
        return ("minimo" if cat0 == "E" else "massimo", True, e0, s1)
    return None


def _decidi(
    campioni: tuple[Campione, ...], indici: tuple[int, ...], griglia: tuple[Decimal, ...],
    verso_richiesto: VersoRichiesto, sessione: Sessione,
) -> Risultato:
    cats = tuple(cat(c) for c in campioni)
    if all(c == "A" for c in cats):
        return tutto_ammissibile(campioni, verso_richiesto, sessione)
    if "A" not in cats:
        return nessun_valore(campioni, verso_richiesto, sessione)
    runs = _runs(cats)
    trovato = _pattern(runs)
    if trovato is None or (verso_richiesto != "auto" and trovato[0] != verso_richiesto):
        return non_monotona(campioni, indici, griglia, verso_richiesto, runs, sessione)
    verso, limite, i_lo, i_hi = trovato
    return bisezione(campioni, indici, griglia, verso, i_lo, i_hi, limite, sessione)  # type: ignore[arg-type]
