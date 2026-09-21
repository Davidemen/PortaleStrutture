"""NTC2018 §4.1.2.1.1.1 — resistenze di calcolo (design strengths)."""
from .tables import ALPHA_CC, GAMMA_C


def fcd(fck_MPa: float, *, gamma_c: float = GAMMA_C, alpha_cc: float = ALPHA_CC) -> float:
    """fcd = alpha_cc*fck/gamma_c, MPa."""
    return alpha_cc * fck_MPa / gamma_c


def fctd(fctk_MPa: float, *, gamma_c: float = GAMMA_C) -> float:
    """fctd = fctk/gamma_c, MPa."""
    return fctk_MPa / gamma_c
