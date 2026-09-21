"""NTC2018 §11.3.2 — tensione di calcolo di snervamento delle armature."""
from .tables import GAMMA_S


def fyd(fyk_MPa: float, *, gamma_s: float = GAMMA_S) -> float:
    """fyd = fyk/gamma_s, MPa."""
    return fyk_MPa / gamma_s
