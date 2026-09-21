"""Mean compressive stress sigma_cp (sheet B13).

Not a divergence: sigma_cp = NEd/Ac, where Ac is the FULL concrete cross-section
(= bw*h for a rectangular web), per NTC2018 §4.1.2.3.5.1 (identical to EN1992-1-1
§6.2.2(1)). The sheet's `bw*h` is correct in both modes; a prior "fix" that divided
by `bw*d` instead inflated sigma_cp (and therefore VRd) and has been reverted.
"""
from strutture.shared.units import kn_to_n

from .tables import SIGMA_CP_MAX_FACTOR


def sigma_cp_MPa(ned_kN: float, bw_mm: float, h_mm: float, fcd_MPa: float) -> float:
    """sigma_cp = MIN(NEd/(bw*h), 0.2*fcd), MPa. Identical in both legacy_compat modes."""
    raw_MPa = kn_to_n(ned_kN) / (bw_mm * h_mm)
    cap_MPa = SIGMA_CP_MAX_FACTOR * fcd_MPa
    return min(cap_MPa, raw_MPa)
