"""Stress under the geometric centre of a loaded rectangle: exact 4-quadrant Newmark sum
(`under_center`) and its pure influence-factor form (`ic_center`), used as an independent QA
cross-check by the elastic-settlement tools (docs/architecture-batch2.md §1.2, spec §"Z6 QA path")."""
from .newmark import newmark_corner


def under_center(q_kPa: float, b_m: float, l_m: float, z_m: float) -> float:
    """Δσz at depth `z_m` beneath the centre of a `b_m` × `l_m` rectangle loaded at `q_kPa`: the
    centre splits the rectangle into 4 equal `(b/2, l/2)` quadrants, each contributing one corner
    term. Approaches `q_kPa` as `z_m -> 0` (the whole load acts directly at the surface)."""
    return 4 * newmark_corner(q_kPa, b_m / 2, l_m / 2, z_m)


def ic_center(b_m: float, l_m: float, z_m: float) -> float:
    """Dimensionless influence factor `Ic = under_center(1, b_m, l_m, z_m)`: the Boussinesq/Newmark
    closed-form centre-stress factor, independent of the numerical layer-by-layer integration —
    the QA cross-check the elastic-settlement tools compare their summed result against."""
    return under_center(1.0, b_m, l_m, z_m)
