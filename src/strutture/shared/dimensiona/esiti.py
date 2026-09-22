"""The non-bisection outcomes: everything admissible, nothing admissible, and the not-monotone
fallback (WORKBENCH_SPEC §23.3 points 3 and 5)."""
import itertools
from decimal import Decimal
from typing import Literal

from .campioni import Campione, Risultato, Sessione, Verso

VersoRichiesto = Literal["auto", "minimo", "massimo"]


def estremo(campioni: tuple[Campione, ...], verso: Verso, valore: Decimal, sessione: Sessione) -> Risultato:
    return Risultato(
        esito="estremo_sufficiente", verso=verso, valore=valore, affidabile=True,
        motivi=(f"Già il valore {valore} soddisfa le verifiche: allargare l'intervallo",),
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
        motivi=(f"Nessun valore dell'intervallo soddisfa le verifiche (il migliore è {migliore.valore})",),
        campioni=campioni, valutazioni=sessione.valutazioni,
    )


def non_monotona(
    campioni: tuple[Campione, ...], indici: tuple[int, ...], griglia: tuple[Decimal, ...],
    verso_richiesto: VersoRichiesto, runs: tuple[tuple[str, int, int], ...], sessione: Sessione,
) -> Risultato:
    verso: Verso = "minimo" if verso_richiesto != "massimo" else "massimo"
    finestre = [(griglia[indici[s]], griglia[indici[e]]) for cat, s, e in runs if cat == "A"]
    testo_finestre = "; ".join(f"[{lo}, {hi}]" for lo, hi in finestre)
    migliore = min((c for c in campioni if c.esito == "ammissibile"), key=lambda c: c.eta_max or 0)
    return Risultato(
        esito="trovato", verso=verso, valore=migliore.valore, affidabile=False,
        motivi=(f"Ammissibile per valori in {testo_finestre}: l'andamento non è monotono, controllare",),
        campioni=campioni, valutazioni=sessione.valutazioni,
    )
