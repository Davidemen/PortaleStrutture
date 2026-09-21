"""Eccentricity and nocciolo d'inerzia (kern) checks for a rigid rectangular footing.

Convention (matches docs/specs/fond-plinti-isolati.md steps 6-8: MYY/eccX from My, MXX/eccY from
Mx): My (moment about the Y axis) bends the footing about Y, so it displaces the pressure resultant
along X -> ex = My/N. Mx bends about X, displacing the resultant along Y -> ey = Mx/N.
"""


def eccentricities(n_kn: float, mx_knm: float, my_knm: float) -> tuple[float, float]:
    """(ex_m, ey_m) for a resultant force N (compression, > 0) with moments Mx, My about the
    footing's centroidal X/Y axes. ex = My/N (along the bx side), ey = Mx/N (along the by side).
    """
    if n_kn <= 0:
        raise ValueError(f"n_kn must be > 0 (compression), got {n_kn}")
    return my_knm / n_kn, mx_knm / n_kn


def in_kern_uniaxial(e_m: float, l_m: float) -> bool:
    """True if a uniaxial eccentricity e (acting along a footing side of length l) keeps the
    whole side in compression: |e| <= l/6.
    """
    return abs(e_m) <= l_m / 6.0


def in_kern_biaxial(ex_m: float, ey_m: float, bx_m: float, by_m: float) -> bool:
    """True if (ex, ey) is within the rectangle's biaxial kern, the diamond |ex|/(bx/6) +
    |ey|/(by/6) <= 1 (every point of the bx * by footing stays in compression).
    """
    return abs(ex_m) / (bx_m / 6.0) + abs(ey_m) / (by_m / 6.0) <= 1.0
