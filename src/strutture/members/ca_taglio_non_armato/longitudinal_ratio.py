"""Longitudinal reinforcement ratio rho_l (sheet B17).

Divergence: the sheet never caps rho_l at 0.02 as required by §4.1.2.3.5.1.
`legacy_compat=True` reproduces the sheet (uncapped); `legacy_compat=False` clamps at RHO_L_MAX.
"""
from strutture.shared.divergences import legacy
from strutture.shared.numeric import clamp

from .tables import RHO_L_MAX


def rho_l_raw(asl_mm2: float, bw_mm: float, d_mm: float) -> float:
    """rho_l = Asl/(bw*d), UNCAPPED. Used to check the §4.1.2.3.5.1 limit even in code-standard
    mode, where `rho_l()` below already returns the capped value used in VRd,1."""
    return asl_mm2 / (bw_mm * d_mm)


def rho_l(asl_mm2: float, bw_mm: float, d_mm: float, *, legacy_compat: bool = False) -> float:
    """rho_l = Asl/(bw*d), capped at 0.02 unless legacy_compat."""
    raw = rho_l_raw(asl_mm2, bw_mm, d_mm)
    if legacy("ca-taglio-non-armato/rho-l-senza-limite", legacy_compat):
        return raw
    return clamp(raw, low=0.0, high=RHO_L_MAX)
