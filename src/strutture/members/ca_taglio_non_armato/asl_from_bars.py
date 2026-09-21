"""Longitudinal steel area from bar count and diameter (sheet `1m` B13, v2 delta #2: N°/Ø
replace the direct Asl scalar of `Foglio1`/v1)."""
import math


def asl_from_barre_mm2(n_barre: int, diametro_barre_mm: float) -> float:
    """Asl = N° * pi*Ø²/4, mm²."""
    return n_barre * math.pi * diametro_barre_mm**2 / 4
