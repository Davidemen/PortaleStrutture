"""Stress at an arbitrary point via signed superposition of 4 sub-rectangles (Fadum method).

Fixes the sheet bug at `500!M/N,AK/AL` (docs/architecture-batch2.md §7): the sheet pairs two
segments of the *same* side of the loaded rectangle into a sub-rectangle ("Ofga" uses (F7, F9),
both segments of the O'd side; "Ocde" uses (F10, F8), both segments of the O'g side) — not a valid
corner rectangle. The correct construction always pairs one segment from each side (`a_i`, one of
the two x-splits, with `b_j`, one of the two y-splits); verified against a brute-force numerical
double integral of the Boussinesq point-load kernel for both an interior and an exterior point
(`tests/shared/soil_stress/test_point.py`, `docs/divergences/soil-stress-fadum-superposition.md`).
"""
from .models import PointStress
from .newmark import newmark_corner


def under_point(q_kPa: float, b_m: float, l_m: float, x_m: float, y_m: float, z_m: float) -> PointStress:
    """Δσz at depth `z_m` under point `(x_m, y_m)`, measured from one corner of a `b_m` × `l_m`
    rectangle loaded at `q_kPa`. The point may be inside or outside the rectangle: each of the two
    axis splits (`x_m`, `b_m - x_m`) and (`y_m`, `l_m - y_m`) can be negative, which flips the sign
    of that sub-rectangle's contribution (the standard "add the overhang, subtract the extension"
    superposition for points outside the loaded footprint)."""
    a1, a2 = x_m, b_m - x_m
    b1, b2 = y_m, l_m - y_m
    parts = (
        _signed_corner(q_kPa, a1, b1, z_m),
        _signed_corner(q_kPa, a2, b1, z_m),
        _signed_corner(q_kPa, a1, b2, z_m),
        _signed_corner(q_kPa, a2, b2, z_m),
    )
    return PointStress(total=sum(parts), parts=parts)


def _signed_corner(q_kPa: float, a_m: float, b_m: float, z_m: float) -> float:
    """`newmark_corner`, extended as an odd function of `a_m` and of `b_m` through zero (a
    zero-width or negative-width split contributes zero or a negated corner term)."""
    if a_m == 0 or b_m == 0:
        return 0.0
    sign = (1 if a_m > 0 else -1) * (1 if b_m > 0 else -1)
    return sign * newmark_corner(q_kPa, abs(a_m), abs(b_m), z_m)
