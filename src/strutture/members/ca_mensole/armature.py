"""Reinforcement areas and minimum tie-steel area (`Mensola tozza!H20,H21,H23`, spec §4 steps 9-11).

`H23`'s two branches (0.25·As,hor vs 0.5·PEd/fyd) are not obviously continuous at a = 0.5h; the
spec (§7) flags this as unverified against the source clause, so both modes keep the sheet's
formula as-is ("Da verificare", `docs/divergences/ca-mensole.md`).
"""
from strutture.shared.units import kn_to_n

from .models import ArmatureResult
from .rebar_helpers import bars_area_or_zero

HALF_HEIGHT_THRESHOLD = 0.5           # a < 0.5h branch threshold (spec §4 step 11)
AS_LNK_REDUCTION_SHORT_SPAN = 0.25    # As,lnk = 0.25*As,hor when a < 0.5h — clause "?" (spec §6)
AS_LNK_FACTOR_LONG_SPAN = 0.5         # As,lnk = 0.5*PEd/fyd when a >= 0.5h — clause "?" (spec §6)


def armature(
    n_hor: int, phi_hor_mm: float, n_incl: int, phi_incl_mm: float, a_mm: float, h_mm: float, ped_kN: float, fyd_MPa: float
) -> ArmatureResult:
    as_hor_mm2 = bars_area_or_zero(n_hor, phi_hor_mm)
    as_incl_mm2 = bars_area_or_zero(n_incl, phi_incl_mm)
    if a_mm < HALF_HEIGHT_THRESHOLD * h_mm:
        as_lnk_min_mm2 = AS_LNK_REDUCTION_SHORT_SPAN * as_hor_mm2
    else:
        as_lnk_min_mm2 = AS_LNK_FACTOR_LONG_SPAN * kn_to_n(ped_kN) / fyd_MPa
    return ArmatureResult(as_hor_mm2=as_hor_mm2, as_incl_mm2=as_incl_mm2, as_lnk_min_mm2=as_lnk_min_mm2)
