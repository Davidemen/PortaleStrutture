"""Step (spec calc steps 10-14, `Neve accumulo!K38/L38/M38/H43`): design shape coeff at the far edge."""
from typing import Final

from strutture.shared.divergences import legacy
from strutture.shared.numeric import clamp

M1_INTERP_MIN: Final[float] = 0.0  # architecture.md §6: FIX — clamp the interpolated m1 (Bug 7)
# Upper bound = accumulo_mw.MW_MAX (Circ. §C3.4.5.6 / EN1991-1-3 §6.2(3): 0.8 <= mu_w <= 4).
# There is no independent cap on the drift shape coefficient other than mu_w's own ceiling; a
# previous MW_INTERP_MAX=2.0 here had no basis in the clause and silently truncated legitimate
# values in (2, 4] (reviewed finding, CRITICAL — see docs/divergences/neve.md).
M1_INTERP_MAX: Final[float] = 4.0


def m1_interpolato(b2_m: float, ls_m: float, mu_w: float, m1_input: float, *, legacy_compat: bool) -> float:
    """`M38`: linear interpolation of m1 between the wall (μw) and the far edge (m1_input) over
    ls, evaluated at b2. Legacy mode reproduces Bug 7 (spec §7.7): nothing clamps the result, so
    it can go negative when b2 is far larger than ls; fixed mode clamps to [0, 4] (4 = mu_w's own
    ceiling per Circ. §C3.4.5.6 / EN1991-1-3 §6.2(3); there is no separate cap of 2).
    """
    slope_per_m = (mu_w - m1_input) / ls_m  # `K38`
    extrapolated_at_b2 = slope_per_m * (ls_m - b2_m)  # `L38`
    interpolated = extrapolated_at_b2 + m1_input
    if legacy("neve/accumulo-m1-interpolato-senza-limiti", legacy_compat):
        return interpolated
    return clamp(interpolated, M1_INTERP_MIN, M1_INTERP_MAX)


def m1_finale(b2_m: float, ls_m: float, mu_w: float, m1_input: float, *, legacy_compat: bool) -> float:
    """`H43`: interpolated value when the lower building is narrower than the drift zone, else the
    manual input unchanged.
    """
    if b2_m < ls_m:
        return m1_interpolato(b2_m, ls_m, mu_w, m1_input, legacy_compat=legacy_compat)
    return m1_input
