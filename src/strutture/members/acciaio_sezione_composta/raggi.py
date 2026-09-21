"""Radii of gyration i = sqrt(I/A)."""
import math


def raggio_giro_mm(inerzia_mm4: float, area_mm2: float) -> float:
    return math.sqrt(inerzia_mm4 / area_mm2)
