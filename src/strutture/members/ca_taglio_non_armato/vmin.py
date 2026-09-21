"""Minimum shear resistance vmin (sheet B16)."""
from .tables import VMIN_COEFF


def vmin_MPa(k: float, fck_MPa: float) -> float:
    """vmin = 0.035*k^1.5*sqrt(fck)."""
    return VMIN_COEFF * k**1.5 * fck_MPa**0.5
