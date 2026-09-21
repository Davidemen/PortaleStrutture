"""Stirrup (staffe) area-per-metre helper, used by the shear-check tools."""
from .diameters import bar_area

MM_PER_M = 1000.0


def asw_per_m(diameter_mm: float, legs: int, spacing_mm: float) -> float:
    """Transverse steel area per running metre, Asw/s * 1000 [mm^2/m].

    `legs` is the number of stirrup legs crossing the shear crack (bracci), typically 2 or 4.
    """
    if legs <= 0:
        raise ValueError(f"legs must be > 0, got {legs}")
    if spacing_mm <= 0:
        raise ValueError(f"spacing_mm must be > 0, got {spacing_mm}")
    return legs * bar_area(diameter_mm) * MM_PER_M / spacing_mm
