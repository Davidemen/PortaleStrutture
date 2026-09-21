"""fck / fcd from a raw Rck input (sheet B2->B4; not a class-table lookup, Rck is a free input)."""
from strutture.shared.materials.concrete import fcd

from .tables import ALPHA_CC, FCK_FROM_RCK_FACTOR, GAMMA_C


def fck_from_rck(rck_MPa: float) -> float:
    """fck = 0.83*Rck (§11.2.10.1), MPa."""
    return FCK_FROM_RCK_FACTOR * rck_MPa


def fcd_from_fck(fck_MPa: float, *, gamma_c: float = GAMMA_C, alpha_cc: float = ALPHA_CC) -> float:
    """fcd = alpha_cc*fck/gamma_c (§4.1.2.1.1.1), MPa."""
    return fcd(fck_MPa, gamma_c=gamma_c, alpha_cc=alpha_cc)
