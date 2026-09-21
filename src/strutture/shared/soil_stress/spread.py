"""Approximate 2:1-type load-spread stress increase, used by the oedometric-settlement sheet
(`docs/specs/geo-cedimenti-edometrico.md` step 2a) as a cheaper alternative to the exact
Newmark/Boussinesq integral (which the sheet keeps in a separate reference column, see
`newmark.newmark_corner`)."""


def spread_2to1(q_kPa: float, b_m: float, l_m: float, z_m: float) -> float:
    """Δσz at depth `z_m` under the centre of a `b_m` × `l_m` rectangle loaded at `q_kPa`, by the
    approximate load-spread formula `q·B·L / ((B+z)(L+z))` (verified bit-exact against
    `build/data/geo-cedimenti/edometrico.csv` column H)."""
    if z_m < 0:
        raise ValueError(f"spread_2to1: z_m must be >= 0, got {z_m}")
    return q_kPa * b_m * l_m / ((b_m + z_m) * (l_m + z_m))
