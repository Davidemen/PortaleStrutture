"""Verified restatement (docs/architecture-phase2.md §6, wave-3 adoption) of the slenderness ratio
h/d (`hd_ratio.py`) and the external pressure coefficients on the windward, side and leeward faces
(`cpe_windward.py`/`cpe_side.py`/`cpe_leeward.py`, all Circ. NTC2019 §C3.3.8.1) for ONE wind
direction. The calculation code is never touched.

`cpe_windward`/`cpe_side` are each a 2-branch piecewise function of h/d (linear ramp, then capped);
the SAME closed-form clamp the roof-shape coefficient of `neve/relazione_falda.py` uses reproduces
both branches with a single formula (verified against the two modules for h/d∈[0,5]), so only the
"h/d>5 → not defined (ND)" branch needs its own handling — that branch has no `Passo` at all (`None`
risultato). `cpe_leeward` has two DIFFERENT slopes either side of its breakpoint (not a simple cap),
so it keeps two distinct formula texts, chosen at trace-build time from the actual h/d like every
other branch-dependent restatement in this codebase (e.g. `ca_travi/relazione_geometria.py::_passo_as`).

`DirectionResult.h_d`/`cpe_windward`/`cpe_side`/`cpe_leeward` share the SAME UI symbol hint between
direction 1 and direction 2 (`VentoCpeOutput.dir1`/`dir2` both being a `DirectionResult`), so every
`Passo.simbolo` here is suffixed "(direzione N)" — free display text, never parsed — to avoid two
different numbers being filed under the identical bare symbol."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .cpe_leeward import (
    LEEWARD_BASE,
    LEEWARD_BASE_2,
    LEEWARD_BREAKPOINT,
    LEEWARD_SLENDER_LIMIT,
    LEEWARD_SLOPE,
    LEEWARD_SLOPE_2,
)
from .cpe_side import SIDE_BASE, SIDE_BREAKPOINT, SIDE_CAP, SIDE_SLOPE
from .cpe_windward import WINDWARD_BASE, WINDWARD_BREAKPOINT, WINDWARD_CAP, WINDWARD_SLOPE
from .models import DirectionResult

CLAUSOLA = "Circ. NTC2019 §C3.3.8.1"


def traccia_direzione(numero: int, descrizione: str, h: float, profondita: float, id_profondita: str, risultato: DirectionResult) -> Traccia:
    """4 passi (h/d, c_pe sopravento, laterale, sottovento) quando h/d ≤ 5, altrimenti solo h/d
    (i coefficienti non sono definiti dalla tabella, "ND")."""
    candidati = (
        _passo_hd(numero, id_profondita, h, profondita, risultato.h_d),
        _passo_cpe_windward(numero, risultato.h_d, risultato.cpe_windward),
        _passo_cpe_side(numero, risultato.h_d, risultato.cpe_side),
        _passo_cpe_leeward(numero, risultato.h_d, risultato.cpe_leeward),
    )
    passi = tuple(passo for passo in candidati if passo is not None)
    return Traccia(titolo=f"Coefficienti di pressione esterna — direzione {numero} ({descrizione})", passi=passi)


def _passo_hd(numero: int, id_profondita: str, h: float, profondita: float, hd_val: float) -> Passo:
    """`cpe_windward.WINDWARD_SLENDER_LIMIT`/`cpe_side.SIDE_SLENDER_LIMIT`/`LEEWARD_SLENDER_LIMIT`
    are the SAME value (5.0, Circ. C3.3.8.1) in each of the three faces' own modules; the "ND"
    note below cites the leeward one only to avoid repeating three identical numbers."""
    nota = f"Rapporto altezza/profondità per la direzione {numero}."
    if hd_val > LEEWARD_SLENDER_LIMIT:
        nota += f" h/{id_profondita} > {LEEWARD_SLENDER_LIMIT:g}: i coefficienti di pressione esterna non sono definiti (ND) dalla tabella per questa direzione."
    return Passo(
        simbolo=f"h/d (direzione {numero})",
        formula=f"h / {id_profondita}",
        valori=(
            Valore(simbolo="h", valore=h, unita="m", descrizione="altezza dell'edificio"),
            Valore(simbolo=id_profondita, valore=profondita, unita="m", descrizione=f"profondità in pianta nella direzione {numero} del vento"),
        ),
        risultato=hd_val, unita="-", clausola=CLAUSOLA, nota=nota,
    )


def _passo_cpe_windward(numero: int, hd: float, cpe: float | None) -> Passo | None:
    if cpe is None:
        return None
    hd_id = f"hd_{numero}"
    return Passo(
        simbolo=f"c_pe,sopravento (direzione {numero})",
        formula=f"min(c_pe,max, c_pe,0 + c_pe,pend * {hd_id})",
        valori=(
            Valore(simbolo="c_pe,max", valore=WINDWARD_CAP, descrizione=f"valore massimo per h/d > {WINDWARD_BREAKPOINT:g}"),
            Valore(simbolo="c_pe,0", valore=WINDWARD_BASE, descrizione="valore base per h/d=0"),
            Valore(simbolo="c_pe,pend", valore=WINDWARD_SLOPE, descrizione=f"pendenza del tratto lineare 0 ≤ h/d ≤ {WINDWARD_BREAKPOINT:g}"),
            Valore(simbolo=hd_id, valore=hd, descrizione=f"rapporto h/d, direzione {numero}, calcolato sopra"),
        ),
        risultato=cpe, unita="-", clausola=CLAUSOLA,
        nota=f"Parete sopravento, direzione {numero}: rampa lineare fino a h/d={WINDWARD_BREAKPOINT:g}, poi valore costante.",
    )


def _passo_cpe_side(numero: int, hd: float, cpe: float | None) -> Passo | None:
    if cpe is None:
        return None
    hd_id = f"hd_{numero}"
    return Passo(
        simbolo=f"c_pe,laterale (direzione {numero})",
        formula=f"max(c_pe,min, c_pe,0 + c_pe,pend * {hd_id})",
        valori=(
            Valore(simbolo="c_pe,min", valore=SIDE_CAP, descrizione=f"valore minimo per h/d > {SIDE_BREAKPOINT:g}"),
            Valore(simbolo="c_pe,0", valore=SIDE_BASE, descrizione="valore base per h/d=0"),
            Valore(simbolo="c_pe,pend", valore=SIDE_SLOPE, descrizione=f"pendenza del tratto lineare 0 ≤ h/d ≤ {SIDE_BREAKPOINT:g}"),
            Valore(simbolo=hd_id, valore=hd, descrizione=f"rapporto h/d, direzione {numero}, calcolato sopra"),
        ),
        risultato=cpe, unita="-", clausola=CLAUSOLA,
        nota=f"Pareti laterali, direzione {numero}: rampa lineare fino a h/d={SIDE_BREAKPOINT:g}, poi valore costante.",
    )


def _passo_cpe_leeward(numero: int, hd: float, cpe: float | None) -> Passo | None:
    if cpe is None:
        return None
    hd_id = f"hd_{numero}"
    if hd <= LEEWARD_BREAKPOINT:
        return Passo(
            simbolo=f"c_pe,sottovento (direzione {numero})",
            formula=f"c_pe,0 + c_pe,pend * {hd_id}",
            valori=(
                Valore(simbolo="c_pe,0", valore=LEEWARD_BASE, descrizione="valore base per h/d=0"),
                Valore(simbolo="c_pe,pend", valore=LEEWARD_SLOPE, descrizione=f"pendenza del primo tratto, 0 ≤ h/d ≤ {LEEWARD_BREAKPOINT:g}"),
                Valore(simbolo=hd_id, valore=hd, descrizione=f"rapporto h/d, direzione {numero}, calcolato sopra"),
            ),
            risultato=cpe, unita="-", clausola=CLAUSOLA,
            nota=f"Parete sottovento, direzione {numero}: primo tratto lineare, 0 ≤ h/d ≤ {LEEWARD_BREAKPOINT:g}.",
        )
    return Passo(
        simbolo=f"c_pe,sottovento (direzione {numero})",
        formula=f"c_pe,0b + c_pe,pendb * ({hd_id} - hd_bp)",
        valori=(
            Valore(simbolo="c_pe,0b", valore=LEEWARD_BASE_2, descrizione=f"valore base del secondo tratto, h/d={LEEWARD_BREAKPOINT:g}"),
            Valore(simbolo="c_pe,pendb", valore=LEEWARD_SLOPE_2, descrizione=f"pendenza del secondo tratto, h/d > {LEEWARD_BREAKPOINT:g}"),
            Valore(simbolo=hd_id, valore=hd, descrizione=f"rapporto h/d, direzione {numero}, calcolato sopra"),
            Valore(simbolo="hd_bp", valore=LEEWARD_BREAKPOINT, descrizione="valore di h/d di transizione tra i due tratti"),
        ),
        risultato=cpe, unita="-", clausola=CLAUSOLA,
        nota=f"Parete sottovento, direzione {numero}: secondo tratto lineare, h/d > {LEEWARD_BREAKPOINT:g}.",
    )
