"""The non-bisection outcomes: everything admissible, nothing admissible, and the not-monotone
fallback (WORKBENCH_SPEC §23.3 points 3 and 5)."""
import itertools
from decimal import Decimal
from typing import Literal

from .bisezione import bisezione
from .campioni import Campione, Risultato, Sessione, Verso

VersoRichiesto = Literal["auto", "minimo", "massimo"]


def _it(valore: Decimal) -> str:
    """Italian decimal comma for a value in a message to the titolare (WORKBENCH_SPEC's own
    convention throughout, e.g. "b in [0,30; 0,45]")."""
    return str(valore).replace(".", ",")


def estremo(campioni: tuple[Campione, ...], verso: Verso, valore: Decimal, sessione: Sessione) -> Risultato:
    return Risultato(
        esito="estremo_sufficiente", verso=verso, valore=valore, affidabile=True,
        motivi=(f"Già il valore {_it(valore)} soddisfa le verifiche: allargare l'intervallo",),
        campioni=campioni, valutazioni=sessione.valutazioni,
    )


def tutto_ammissibile(campioni: tuple[Campione, ...], verso_richiesto: VersoRichiesto, sessione: Sessione) -> Risultato:
    """When `verso` is forced, "smallest"/"largest admissible" is unambiguous even with everything
    admissible: `da`/`a` itself already IS that extreme. The η trend only disambiguates `"auto"`."""
    if verso_richiesto == "minimo":
        return estremo(campioni, "minimo", campioni[0].valore, sessione)
    if verso_richiesto == "massimo":
        return estremo(campioni, "massimo", campioni[-1].valore, sessione)
    etas = [c.eta_max for c in campioni]
    verso: Verso = "minimo"
    if all(v is not None for v in etas):
        if _strettamente(etas, crescente=True):
            return estremo(campioni, "massimo", campioni[-1].valore, sessione)
        if _strettamente(etas, crescente=False):
            return estremo(campioni, "minimo", campioni[0].valore, sessione)
    return Risultato(
        esito="estremo_sufficiente", verso=verso, valore=None, affidabile=True,
        motivi=("Tutto l'intervallo soddisfa le verifiche: scegliere Valore minimo o Valore massimo",),
        campioni=campioni, valutazioni=sessione.valutazioni,
    )


def _strettamente(valori: list[float | None], *, crescente: bool) -> bool:
    coppie = itertools.pairwise(valori)
    return all((b > a) if crescente else (b < a) for a, b in coppie)


def nessun_valore(campioni: tuple[Campione, ...], verso_richiesto: VersoRichiesto, sessione: Sessione) -> Risultato:
    verso: Verso = "minimo" if verso_richiesto != "massimo" else "massimo"
    migliore = min((c for c in campioni if c.eta_max is not None), key=lambda c: c.eta_max or 0, default=campioni[0])
    return Risultato(
        esito="nessun_valore", verso=verso, valore=None, affidabile=True,
        motivi=(f"Nessun valore dell'intervallo soddisfa le verifiche (il migliore è {_it(migliore.valore)})",),
        campioni=campioni, valutazioni=sessione.valutazioni,
    )


def non_monotona(
    campioni: tuple[Campione, ...], indici: tuple[int, ...], griglia: tuple[Decimal, ...],
    verso_richiesto: VersoRichiesto, runs: tuple[tuple[str, int, int], ...], sessione: Sessione,
) -> Risultato:
    """§23.3 point 5: several alternating admissible/non-admissible bands. Reports the extreme
    edge of the band closest to the direction actually being searched -- the LEFTMOST admissible
    run's near edge for "minimo", the RIGHTMOST one's for "massimo" -- refined by bisection against
    its immediate neighbour (reusing `bisezione`'s own loop, `limite=False`: this is not a validity
    gap), not just the sampled admissible point with the lowest η anywhere in the interval."""
    verso: Verso = "minimo" if verso_richiesto != "massimo" else "massimo"
    finestre = [(griglia[indici[s]], griglia[indici[e]]) for cat, s, e in runs if cat == "A"]
    testo_finestre = "; ".join(f"[{_it(lo)}, {_it(hi)}]" for lo, hi in finestre)
    motivo_finestre = f"Ammissibile per valori in {testo_finestre}: l'andamento non è monotono, controllare"
    a_runs = [(s, e) for cat, s, e in runs if cat == "A"]
    scelta = a_runs[0] if verso == "minimo" else a_runs[-1]
    posizione_bordo, posizione_vicino = (scelta[0], scelta[0] - 1) if verso == "minimo" else (scelta[1], scelta[1] + 1)
    if not (0 <= posizione_vicino < len(indici)):
        # The chosen run already touches the sampled interval's own edge: nothing to refine against.
        bordo = next(c for c in campioni if c.valore == griglia[indici[posizione_bordo]])
        return Risultato(
            esito="trovato", verso=verso, valore=bordo.valore, affidabile=False,
            motivi=(motivo_finestre,), campioni=campioni, valutazioni=sessione.valutazioni,
        )
    i_lo, i_hi = (posizione_vicino, posizione_bordo) if verso == "minimo" else (posizione_bordo, posizione_vicino)
    raffinato = bisezione(campioni, indici, griglia, verso, i_lo, i_hi, False, sessione)
    if raffinato.esito == "interrotta":
        return raffinato
    return Risultato(
        esito="trovato", verso=verso, valore=raffinato.valore, affidabile=False,
        motivi=(motivo_finestre, *raffinato.motivi), campioni=raffinato.campioni, valutazioni=raffinato.valutazioni,
    )
