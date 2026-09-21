"""Step: strut inclination cotθ (EC2 6.2.3), rows CX39-CX43 / Z13.

The spec (docs/specs/ca-pilastri.md §4.4/§7.4) flags this as an Excel iterative circular
reference. Reading the raw cellmap formulas shows otherwise: sin²θ (CX42) depends only on the
stirrup geometry, fyd/fcd and `ac` — never on cotθ itself (CX40/Z13) — so cotθ is a direct
one-shot computation, not a fixed point; `shared.numeric.fixpoint` is not needed here.

`nu1` (the strut-efficiency factor in the denominator, VRd,max's own ν1) defaults to 0.5, the
NTC2008/NTC2018 value; the EC2 branch uses ν1=0.6*(1-fck/250) (`limiti_ec2.nu1`) instead — the SAME
ν1 already passed into `taglio_resistenza.vrdc` — so the θ returned here balances VRd,s and
VRd,max consistently for either norm (review finding, MEDIUM: this used to hardcode 0.5
regardless of norma, so EC2's reported cotθ was inconsistent with its own echoed ν1).
"""
import math

from strutture.shared.numeric import clamp

COT_THETA_MIN = 1.0
COT_THETA_MAX = 2.5
NU1_NTC_FISSO = 0.5  # NTC2008/NTC2018: coefficiente ν1 fisso, non da formula (v. taglio_resistenza.py)


def cot_theta(diametro_staffe_mm: float, fyd_MPa: float, larghezza_mm: float, passo_staffe_mm: float, ac: float, fcd_MPa: float, *, nu1: float = NU1_NTC_FISSO) -> float:
    """CX42 (sin²θ), CX43 (cotθ grezzo), Z13 (clamp EC2 6.2.3(2) in [1, 2.5])."""
    area_staffe_mm2 = math.pi * diametro_staffe_mm**2 / 4.0 * 2.0  # due bracci
    sin2_theta = (area_staffe_mm2 * fyd_MPa) / (larghezza_mm * passo_staffe_mm * (ac * nu1 * fcd_MPa))
    cot_theta_raw = math.sqrt((1.0 - sin2_theta) / sin2_theta)
    return clamp(cot_theta_raw, COT_THETA_MIN, COT_THETA_MAX)
