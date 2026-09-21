"""Cracked (stage-II) elastic analysis of a rectangular RC section, n=15 homogenisation.

Source: `docs/specs/ca-travi.md` Tool 4 `verifica-sle-tensioni`, step `y [Z38]`:
    y = (n*As/b) * (-1 + sqrt(1 + 2*b*d/(n*As)))
which is the closed-form root of the singly-reinforced first-moment-of-area equation
    0.5*b*x^2 = n*As*(d - x).
Generalised here to doubly-reinforced sections (compression steel As2 at depth d2), which
reduces to the sheet's formula exactly when As2=0:
    0.5*b*x^2 + [(n-1)*As2 + n*As]*x - [(n-1)*As2*d2 + n*As*d] = 0
"""
import math

from .models import CrackedSectionResult

DEFAULT_HOMOGENISATION_N = 15.0


def cracked_neutral_axis(b_mm: float, d_mm: float, d2_mm: float, as_mm2: float, as2_mm2: float,
                          n: float = DEFAULT_HOMOGENISATION_N) -> CrackedSectionResult:
    """Neutral-axis depth x and cracked inertia Ii of a rectangular section.

    b_mm: section width. d_mm: effective depth of tension steel As. d2_mm: depth of
    compression steel As2 (from the compressed fibre). as_mm2/as2_mm2: tension/compression
    steel areas (as2_mm2=0 for a singly-reinforced section). n: Es/Ec homogenisation ratio.
    """
    if b_mm <= 0:
        raise ValueError(f"b_mm must be > 0, got {b_mm}")
    if d_mm <= 0:
        raise ValueError(f"d_mm must be > 0, got {d_mm}")
    if d2_mm < 0 or d2_mm >= d_mm:
        raise ValueError(f"d2_mm must be in [0, d_mm), got d2_mm={d2_mm}, d_mm={d_mm}")
    if as_mm2 < 0 or as2_mm2 < 0:
        raise ValueError(f"as_mm2 and as2_mm2 must be >= 0, got as_mm2={as_mm2}, as2_mm2={as2_mm2}")
    if n <= 0:
        raise ValueError(f"n must be > 0, got {n}")
    if as_mm2 == 0 and as2_mm2 == 0:
        raise ValueError("at least one of as_mm2, as2_mm2 must be > 0")

    b_coef = (n - 1.0) * as2_mm2 + n * as_mm2
    c_coef = (n - 1.0) * as2_mm2 * d2_mm + n * as_mm2 * d_mm
    x = (-b_coef + math.sqrt(b_coef**2 + 2.0 * b_mm * c_coef)) / b_mm

    inertia = (
        b_mm * x**3 / 3.0
        + n * as_mm2 * (d_mm - x) ** 2
        + (n - 1.0) * as2_mm2 * (x - d2_mm) ** 2
    )
    return CrackedSectionResult(x_mm=x, inertia_cracked_mm4=inertia)
