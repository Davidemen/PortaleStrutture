"""Spec step 1: effective depth. `dy` is nested under `dx` (subtracts the full φx then half φy),
as in the sheet's own D11 formula — not a bug, just how the two curtains of bars stack."""


def effective_depth(h_mm: float, cover_mm: float, phix_mm: float, phiy_mm: float) -> tuple[float, float, float]:
    """Returns (dx, dy, d=(dx+dy)/2), all in mm."""
    dx_mm = h_mm - cover_mm - phix_mm / 2.0
    dy_mm = h_mm - cover_mm - phix_mm - phiy_mm / 2.0
    d_mm = (dx_mm + dy_mm) / 2.0
    return dx_mm, dy_mm, d_mm


def column_shape(lato_a_mm: float) -> str:
    """'circ' when the column side A is 0 (sheet convention: use the diameter instead), else 'rett'."""
    return "circ" if lato_a_mm == 0 else "rett"
