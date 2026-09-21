"""Concrete and steel constitutive laws, NTC 2018 §4.1.2.1.2.1 (≤ C50/60) — pure `σ(ε)` functions.

**Sign convention** (documented once, used by every function here and by `integrazione.py`):
strain and stress are signed with **tension positive, compression negative** (standard continuum
mechanics convention — "compression negative" per `docs/architecture-phase4.md` §A). Concrete
never carries tension (`σ = 0` for `ε >= 0`). This is the internal engine convention; the public
result reported by `integrazione.py` negates N/Mx/My so that N > 0 means compression, matching the
Italian engineering convention stated in the architecture.

Concrete: parabola-rectangle (Fig. 4.1.2.1.2.1a, default) and the bilinear/"rectangular" diagram
(Fig. 4.1.2.1.2.1b, εc3/εcu3) — both valid up to C50/60, exponent n = 2.
Steel: elastic-perfectly-plastic (default, unlimited strain) and bilinear with hardening
`k = ft/fy`, ultimate strain `εud = 0.9·εuk` (`εuk = 0.075` for B450C is the module default; pass
`eps_uk_mm_per_mm` explicitly for another grade).
"""
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING

from strutture.shared.numeric import clamp

if TYPE_CHECKING:
    from .modelli import MaterialiSezione

EPS_C2 = 0.002  # NTC2018 §4.1.2.1.2.1 — deformazione al picco, parabola-rettangolo.
EPS_CU2 = 0.0035  # deformazione ultima, parabola-rettangolo.
EPS_C3 = 0.00175  # deformazione al picco, diagramma bilineare/rettangolare.
EPS_CU3 = 0.0035  # deformazione ultima, diagramma bilineare/rettangolare.
ESPONENTE_PARABOLA = 2  # NTC2018 §4.1.2.1.2.1 — esponente n della parabola (valido fino a C50/60).
EPS_UK_B450C = 0.075  # NTC2018 Tab. 11.3.Ib — deformazione caratteristica a rottura, B450C.


def sigma_calcestruzzo_parabola_rettangolo(eps: float, fcd_MPa: float) -> float:
    """Legge parabola-rettangolo. Trazione ignorata; oltre εcu2 resta sul plateau (robustezza
    numerica: la Parte 2 vincola la fibra estrema a ≤ εcu2)."""
    if eps >= 0.0:
        return 0.0
    m = -eps
    if m <= EPS_C2:
        return -fcd_MPa * (1.0 - (1.0 - m / EPS_C2) ** ESPONENTE_PARABOLA)
    return -fcd_MPa


def sigma_calcestruzzo_bilineare(eps: float, fcd_MPa: float) -> float:
    """Legge bilineare/rettangolare (rampa lineare fino a εc3, poi plateau a fcd fino a εcu3)."""
    if eps >= 0.0:
        return 0.0
    m = -eps
    if m <= EPS_C3:
        return -fcd_MPa * (m / EPS_C3)
    return -fcd_MPa


def eps_ud(eps_uk_mm_per_mm: float = EPS_UK_B450C) -> float:
    """εud = 0.9·εuk — deformazione ultima di progetto dell'acciaio (pivot A)."""
    return 0.9 * eps_uk_mm_per_mm


def sigma_acciaio_elastico_perfettamente_plastico(eps: float, fyd_MPa: float, es_MPa: float) -> float:
    """Elastico-perfettamente-plastico, deformazione illimitata (ramo orizzontale)."""
    return clamp(es_MPa * eps, -fyd_MPa, fyd_MPa)


def sigma_acciaio_bilineare(
    eps: float, fyd_MPa: float, es_MPa: float, k_incrudimento: float, eps_uk_mm_per_mm: float = EPS_UK_B450C,
) -> float:
    """Bilineare con incrudimento `k = ft/fy`, tratto lineare fino a εud = 0.9·εuk (oltre εud resta
    sul valore raggiunto a εud: la Parte 2 vincola la fibra estrema a ≤ εud, pivot A)."""
    eps_yd = fyd_MPa / es_MPa
    m = min(abs(eps), eps_ud(eps_uk_mm_per_mm))
    segno = 1.0 if eps >= 0.0 else -1.0
    if m <= eps_yd:
        return segno * es_MPa * m
    eud = eps_ud(eps_uk_mm_per_mm)
    sigma_ud = k_incrudimento * fyd_MPa
    frazione = (m - eps_yd) / (eud - eps_yd) if eud > eps_yd else 1.0
    return segno * (fyd_MPa + (sigma_ud - fyd_MPa) * frazione)


def legge_calcestruzzo(materiali: "MaterialiSezione") -> Callable[[float], float]:
    """`σ(ε)` per il calcestruzzo, selezionata da `materiali.legge_calcestruzzo`."""
    fcd_MPa = materiali.calcestruzzo.fcd_MPa
    if materiali.legge_calcestruzzo == "parabola-rettangolo":
        return partial(sigma_calcestruzzo_parabola_rettangolo, fcd_MPa=fcd_MPa)
    return partial(sigma_calcestruzzo_bilineare, fcd_MPa=fcd_MPa)


def legge_acciaio(materiali: "MaterialiSezione") -> Callable[[float], float]:
    """`σ(ε)` per l'acciaio, selezionata da `materiali.legge_acciaio`."""
    acciaio = materiali.acciaio
    if materiali.legge_acciaio == "elastico-perfettamente-plastico":
        return partial(sigma_acciaio_elastico_perfettamente_plastico, fyd_MPa=acciaio.fyd_MPa, es_MPa=acciaio.es_MPa)
    k = acciaio.ftk_MPa / acciaio.fyk_MPa
    return partial(sigma_acciaio_bilineare, fyd_MPa=acciaio.fyd_MPa, es_MPa=acciaio.es_MPa, k_incrudimento=k)
