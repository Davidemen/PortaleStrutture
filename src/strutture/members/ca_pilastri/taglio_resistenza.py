"""Step: shear capacity VRd = min(VRd,c, VRd,s) — EC2 6.2.3 / NTC2018 §4.1.2.1.3.2, rows Z15-Z17."""
import math

from strutture.shared.units import n_to_kn

STIRRUP_INCLINATION_DEG = 90.0  # Z14: inclinazione delle staffe rispetto all'asse (staffe verticali)
STIRRUP_LEGS = 2  # bracci delle staffe (formule Z15/Z16 moltiplicano l'area per 2)
NU1_NTC_FISSO = 0.5  # NTC2008/NTC2018 (entrambe le modalità): coefficiente ν1 fisso, non da formula


def _cot_alpha() -> float:
    return 1.0 / math.tan(math.radians(STIRRUP_INCLINATION_DEG))


def vrdc(z_mm: float, larghezza_mm: float, ac: float, fcd_MPa: float, cot_theta_: float, *, nu1: float = NU1_NTC_FISSO) -> float:
    """Z15: taglio resistente lato calcestruzzo (puntoni compressi). `nu1` è fisso a 0.5 per
    NTC2008/NTC2018; il foglio EC2 lo sostituisce con `limiti_ec2.nu1(cls, ...)` (EC2 §6.2.2(6))."""
    cot_alpha = _cot_alpha()
    return n_to_kn(z_mm * larghezza_mm * ac * nu1 * fcd_MPa * (cot_alpha + cot_theta_) / (1.0 + cot_theta_**2))


def vrds(z_mm: float, diametro_staffe_mm: float, passo_staffe_mm: float, fyd_MPa: float, cot_theta_: float) -> float:
    """Z16: taglio resistente lato armatura trasversale (staffe)."""
    cot_alpha = _cot_alpha()
    area_staffe_mm2 = math.pi * diametro_staffe_mm**2 / 4.0 * STIRRUP_LEGS
    sin_alpha = math.sin(math.radians(STIRRUP_INCLINATION_DEG))
    return n_to_kn(z_mm * area_staffe_mm2 / passo_staffe_mm * fyd_MPa * (cot_alpha + cot_theta_) * sin_alpha)
