"""Step (spec calc steps 6/8/9, `Neve!H32/H54/H58`): roof shape coefficient μ, NTC2018 §3.4.5.2
Tab. 3.4.II (~ EN1991-1-3 Tab. 5.2)."""
from typing import Final

MU_FLAT: Final[float] = 0.8  # 0-30°, and always when a barrier holds the snow at the lower eave
MU_STEEP: Final[float] = 0.0  # >=60°
ANGLE_LOW_DEG: Final[float] = 30.0
ANGLE_HIGH_DEG: Final[float] = 60.0


def coefficiente_forma(angle_deg: float, parapetto: bool, *, legacy_compat: bool) -> float:
    """μ for a single pitch. `parapetto=True` forces μ=0.8 regardless of angle (`Neve!H31/H53/H57`).

    Fixed mode: continuous 0.8 -> 0 ramp over [30°, 60°), i.e. `30 <= a < 60`.
    Legacy mode reproduces Bug 6 (`docs/specs/neve.md` §7.6): the sheet's `AND(a>30, a<60)` is
    strict on both ends, so a=30° exactly falls through to the else branch (μ=0) instead of the
    ramp's 0.8, a discontinuity versus the a<30° branch which still returns 0.8 up to (not
    including) 30°.
    """
    if parapetto:
        return MU_FLAT
    if angle_deg < ANGLE_LOW_DEG:
        return MU_FLAT
    on_ramp = (
        ANGLE_LOW_DEG < angle_deg < ANGLE_HIGH_DEG
        if legacy_compat
        else ANGLE_LOW_DEG <= angle_deg < ANGLE_HIGH_DEG
    )
    if on_ramp:
        return MU_FLAT * (ANGLE_HIGH_DEG - angle_deg) / (ANGLE_HIGH_DEG - ANGLE_LOW_DEG)
    return MU_STEEP
