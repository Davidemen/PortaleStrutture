"""Newmark (1942) / Steinbrenner corner-of-rectangle vertical-stress influence factor.

Reference: Poulos & Davis, "Elastic Solutions for Soil and Rock Mechanics" — the classical closed
form for the increase in vertical stress Δσz at depth z beneath a CORNER of a flexible rectangle
(sides a, b) uniformly loaded with pressure q. Verified bit-exact (rel<1e-9) against the sheet
`500`'s own `qv` column (`build/data/geo-cedimenti/500.csv`, sub-rectangle "Ofga", a=b=2000 cm,
q=0.8 kg/cmq, z=10..810 cm) and against the textbook reference value Iz(m=1, n=1) = 0.175.
"""
import math


def newmark_corner(q_kPa: float, a_m: float, b_m: float, z_m: float) -> float:
    """Δσz [kPa] at depth `z_m` beneath a corner of an `a_m` × `b_m` rectangle loaded at `q_kPa`.

    `m = a/z`, `n = b/z`; `den = 1 + m² + n²`, `num = (m·n)²`. The arctan term needs the `+π`
    branch correction when `den < num` (equivalently `m²+n²+1 < m²n²`) to stay on the continuous
    branch of the influence factor as `den − num` changes sign (task/architecture-batch2.md §1.2).
    """
    if z_m <= 0:
        raise ValueError(f"newmark_corner: z_m must be > 0, got {z_m}")
    if a_m < 0 or b_m < 0:
        raise ValueError(f"newmark_corner: a_m, b_m must be >= 0, got a_m={a_m}, b_m={b_m}")
    m, n = a_m / z_m, b_m / z_m
    den = 1 + m**2 + n**2
    num = (m * n) ** 2
    sqrt_den = math.sqrt(den)
    term1 = 2 * m * n * sqrt_den * (den + 1) / ((den + num) * den)
    term2 = _arctan_branch(m, n, den, num, sqrt_den)
    return q_kPa / (4 * math.pi) * (term1 + term2)


def _arctan_branch(m: float, n: float, den: float, num: float, sqrt_den: float) -> float:
    """`atan(2mn·√den / (den−num))`, continuous across the `den == num` singularity (+π/2 limit,
    +π correction beyond it) — see `newmark_corner`'s docstring."""
    if num == den:
        return math.pi / 2
    angle = math.atan(2 * m * n * sqrt_den / (den - num))
    return angle + math.pi if num > den else angle
