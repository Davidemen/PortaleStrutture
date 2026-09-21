"""Spec steps 2/5-7: control-perimeter length u(a) and enclosed area A_a(a) at distance `a` from the
column face. `u(a)` is the standard EC2§6.4.2 rounded-rectangle/circle formula in both modes (it already
matches the sheet exactly). `A_a(a)` diverges: the sheet always uses `A*B + 4*MIN(A,B)*a + pi*a^2`
(docs/architecture-batch2.md §1 `ec2_shear.control_perimeter` note) even for circular columns, where it
silently drops the circular term (`A=lato_a_mm=0`); the code-standard branch uses the shape-aware area
from `shared.ec2_shear.control_perimeter` instead."""
import math

from strutture.shared.ec2_shear import control_perimeter

from .effective_depth import column_shape


def perimeter_length_mm(lato_a_mm: float, lato_b_mm: float, diametro_mm: float, dist_mm: float, umanuale_mm: float | None) -> float:
    """u(a), capped by the manual override `umanuale_mm` (sheet: MIN(umanuale, u(a)))."""
    shape = column_shape(lato_a_mm)
    a_mm = diametro_mm if shape == "circ" else lato_a_mm
    u_mm = control_perimeter(shape, a_mm, lato_b_mm, dist_mm).u_mm
    return u_mm if umanuale_mm is None else min(umanuale_mm, u_mm)


def area_within_perimeter_mm2(lato_a_mm: float, lato_b_mm: float, diametro_mm: float, dist_mm: float, *, legacy_compat: bool) -> float:
    """A_a(a): legacy sheet formula (unconditional on shape) or shape-aware code-standard formula."""
    if legacy_compat:
        return lato_a_mm * lato_b_mm + 4.0 * min(lato_a_mm, lato_b_mm) * dist_mm + math.pi * dist_mm**2
    shape = column_shape(lato_a_mm)
    a_mm = diametro_mm if shape == "circ" else lato_a_mm
    return control_perimeter(shape, a_mm, lato_b_mm, dist_mm).area_mm2
