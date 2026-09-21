"""Crack-spacing branch for `ca-apertura-fessure` (Circ. 2019 §C4.1.7/§C4.1.10), calc steps 8-11.

The §C4.1.10 branch [`E14`] uses `h` and `x` directly (`k*(h-x)`) rather than a crack-spacing
formula built from the same k1..k4/c/ø/ρ family as the §C4.1.7 branch. The sheet's `k=0.75` is
kept under `legacy_compat=True`; EN1992-1-1 eq. 7.14 / Circ. 2019 §C4.1.10 give
`sr,max = 1.3*(h-x)` when the bar spacing exceeds `5*(c+ø/2)`, which — since `wk = 1.7*εsm*Δsm`
— corresponds to `k = 1.3/1.7`, used under `legacy_compat=False`. See
docs/divergences/ca-fessurazione.md."""
from typing import Literal

from strutture.shared.divergences import legacy

FATTORE_SPAZIATURA_LIMITE = 5.0  # §C4.1.7 soglia di applicabilità, slim = 5*(c+øeq/2) [E12]
FATTORE_DIVISIONE_C4_1_7 = 1.7  # §C4.1.5/§C4.1.7 [E13]
FATTORE_DELTA_SM_C4_1_10_LEGACY = 0.75  # foglio [E14] — 1.3/1.7 arrotondato per difetto
FATTORE_DELTA_SM_C4_1_10 = 1.3 / 1.7  # EN1992-1-1 eq. 7.14 / Circ. 2019 §C4.1.10: sr,max=1.3*(h-x)

RamoSpaziatura = Literal["C4.1.7", "C4.1.10"]


def spaziatura_limite_mm(copriferro_mm: float, phi_eq_mm: float) -> float:
    """slim = 5*(c + øeq/2) [E12]."""
    return FATTORE_SPAZIATURA_LIMITE * (copriferro_mm + phi_eq_mm / 2)


def delta_sm_c4_1_7_mm(k3: float, copriferro_mm: float, k1: float, k2: float, k4: float, phi_eq_mm: float, rho_eff: float) -> float:
    """Δsm = (k3*c + k1*k2*k4*øeq/ρreff) / 1.7 [E13], §C4.1.7."""
    if rho_eff <= 0:
        raise ValueError("rho_eff deve essere positivo")
    return (k3 * copriferro_mm + k1 * k2 * k4 * phi_eq_mm / rho_eff) / FATTORE_DIVISIONE_C4_1_7


def delta_sm_c4_1_10_mm(h_mm: float, x_mm: float, *, legacy_compat: bool = False) -> float:
    """Δsm = k*(h-x) [E14], §C4.1.10 — vedi nota di modulo per il valore di k."""
    fattore = (
        FATTORE_DELTA_SM_C4_1_10_LEGACY
        if legacy("ca-fessurazione/costante-delta-sm-arrotondata", legacy_compat)
        else FATTORE_DELTA_SM_C4_1_10
    )
    return fattore * (h_mm - x_mm)


def ramo_spaziatura(interferro_mm: float, slim_mm: float) -> RamoSpaziatura:
    """Ramo = IF(s<slim, "C4.1.7", "C4.1.10") [H12]."""
    return "C4.1.7" if interferro_mm < slim_mm else "C4.1.10"


def delta_sm_effettivo_mm(ramo: RamoSpaziatura, delta_c4_1_7_mm: float, delta_c4_1_10_mm: float) -> float:
    """Δsm,eff = IF(s<slim, Δsm(C4.1.7), Δsm(C4.1.10)) [E15]."""
    return delta_c4_1_7_mm if ramo == "C4.1.7" else delta_c4_1_10_mm
