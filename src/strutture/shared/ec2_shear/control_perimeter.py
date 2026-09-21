"""EN 1992-1-1 §6.4.2 basic control perimeter u at distance `dist_mm` from a rectangular or circular
column/pile. Code-standard rounded-rectangle formula (area = a*b + 2*(a+b)*dist + pi*dist^2); the source
sheet instead uses `4*MIN(a,b)*dist` (only equal to the standard term when a == b) — kept only inside the
consuming tool under `legacy_compat=True`, see docs/divergences/ec2-shared.md."""
import math
from typing import Literal

from .models import ControlPerimeter

Shape = Literal["rett", "circ"]


def control_perimeter(shape: Shape, a_mm: float, b_mm: float | None, dist_mm: float) -> ControlPerimeter:
    """`a_mm`/`b_mm` are the rectangular column sides (rett) or `a_mm` is the diameter (circ, `b_mm` ignored)."""
    if a_mm <= 0:
        raise ValueError(f"a_mm must be positive, got {a_mm}")
    if dist_mm < 0:
        raise ValueError(f"dist_mm must be non-negative, got {dist_mm}")

    if shape == "circ":
        radius = a_mm / 2.0
        return ControlPerimeter(
            u_mm=math.pi * (a_mm + 2.0 * dist_mm),
            area_mm2=math.pi * (radius + dist_mm) ** 2,
        )
    if shape == "rett":
        if b_mm is None or b_mm <= 0:
            raise ValueError(f"b_mm must be positive for shape 'rett', got {b_mm}")
        return ControlPerimeter(
            u_mm=2.0 * (a_mm + b_mm) + 2.0 * math.pi * dist_mm,
            area_mm2=a_mm * b_mm + 2.0 * (a_mm + b_mm) * dist_mm + math.pi * dist_mm**2,
        )
    raise ValueError(f"unknown shape {shape!r}, expected 'rett' or 'circ'")
