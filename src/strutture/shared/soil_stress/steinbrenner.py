"""Timoshenko & Goodier displacement-influence factor `IS = I1 + (1-2μ)/(1-μ)·I2`
(`docs/specs/geo-cedimenti-elastico.md` Tool 2, steps 3-5), used by the flexible-rectangle
settlement tool. Verified against the spec's golden case (a=L/B=1, μ=0.35): `IS(1, 10, 0.35) =
0.505131` (centre, b=2H/B), `IS(1, 5, 0.35) = 0.451165` (edge midpoint, b=H/B)."""
import math


def steinbrenner_is(m: float, n: float, mu: float) -> float:
    """`IS(m, n, μ)` for a flexible rectangular foundation: `m = L/B` (aspect ratio), `n` = the
    depth ratio (`2H/B` at the centre, `H/B` at an edge midpoint — the caller picks which), `μ` =
    soil Poisson ratio."""
    if not 0 <= mu < 0.5:
        raise ValueError(f"steinbrenner_is: mu must be in [0, 0.5), got {mu}")
    if m <= 0 or n <= 0:
        raise ValueError(f"steinbrenner_is: m, n must be > 0, got m={m}, n={n}")
    return _i1(m, n) + (1 - 2 * mu) / (1 - mu) * _i2(m, n)


def _i1(m: float, n: float) -> float:
    term1 = m * math.log((1 + math.sqrt(m**2 + 1)) * math.sqrt(m**2 + n**2) / m / (1 + math.sqrt(m**2 + n**2 + 1)))
    term2 = math.log((m + math.sqrt(m**2 + 1)) * math.sqrt(1 + n**2) / (m + math.sqrt(m**2 + n**2 + 1)))
    return (term1 + term2) / math.pi


def _i2(m: float, n: float) -> float:
    return n / (2 * math.pi) * math.atan(m / n / math.sqrt(m**2 + n**2 + 1))
