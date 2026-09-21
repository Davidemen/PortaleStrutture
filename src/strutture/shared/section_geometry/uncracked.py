"""Elastic properties of the full (uncracked) cross-section: rectangle and circle."""
import math

from .models import SectionProperties


def rect(b_mm: float, h_mm: float) -> SectionProperties:
    """Rectangular section b x h, bending about the horizontal centroidal axis."""
    if b_mm <= 0 or h_mm <= 0:
        raise ValueError(f"b_mm and h_mm must be > 0, got b_mm={b_mm}, h_mm={h_mm}")
    area = b_mm * h_mm
    inertia = b_mm * h_mm**3 / 12.0
    return SectionProperties(
        area_mm2=area,
        inertia_mm4=inertia,
        radius_of_gyration_mm=math.sqrt(inertia / area),
        section_modulus_mm3=inertia / (h_mm / 2.0),
    )


def circle(diameter_mm: float) -> SectionProperties:
    """Circular section of diameter D."""
    if diameter_mm <= 0:
        raise ValueError(f"diameter_mm must be > 0, got {diameter_mm}")
    area = math.pi / 4.0 * diameter_mm**2
    inertia = math.pi / 64.0 * diameter_mm**4
    return SectionProperties(
        area_mm2=area,
        inertia_mm4=inertia,
        radius_of_gyration_mm=math.sqrt(inertia / area),
        section_modulus_mm3=inertia / (diameter_mm / 2.0),
    )


def equivalent_square(area_mm2: float) -> float:
    """Side length of the square with the same area A (used for equivalent-section checks)."""
    if area_mm2 <= 0:
        raise ValueError(f"area_mm2 must be > 0, got {area_mm2}")
    return math.sqrt(area_mm2)
