"""`ΔH = q·(B or B/2·4)·μ-term/Es·IS·IF` (`docs/specs/geo-cedimenti-elastico.md` Tool 2, steps 8-9).

Fixes the `(1-μ)` typo (`docs/architecture-batch2.md` §7 "T-G-3 N17/P17"): classical
Timoshenko & Goodier settlement uses `(1-μ²)` (`IS` itself already correctly uses the unsquared
`(1-2μ)/(1-μ)` sub-term, that one is not a bug). `legacy_compat=True` reproduces `(1-μ)`.
"""
from strutture.shared.divergences import legacy
from strutture.shared.units import KPA_PER_MPA, MM_PER_M

QUADRANTS_CENTRO = 4  # 4-quadrant superposition needed to reach the centre point


def _mu_term(mu: float, *, legacy_compat: bool) -> float:
    is_legacy = legacy("geo-cedimenti-elastico/timoshenko-goodier-coefficiente-1-meno-mu", legacy_compat)
    return (1 - mu) if is_legacy else (1 - mu**2)


def deltah_centro_mm(q_kPa: float, b_m: float, mu: float, es_MPa: float, is_centro: float, if_centro: float, *, legacy_compat: bool = False) -> float:
    settlement_m = (q_kPa / KPA_PER_MPA) * (b_m / 2) * _mu_term(mu, legacy_compat=legacy_compat) / es_MPa * is_centro * if_centro * QUADRANTS_CENTRO
    return settlement_m * MM_PER_M


def deltah_bordo_mm(q_kPa: float, b_m: float, mu: float, es_MPa: float, is_bordo: float, if_bordo: float, *, legacy_compat: bool = False) -> float:
    settlement_m = (q_kPa / KPA_PER_MPA) * b_m * _mu_term(mu, legacy_compat=legacy_compat) / es_MPa * is_bordo * if_bordo
    return settlement_m * MM_PER_M
