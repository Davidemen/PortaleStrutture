"""Rigid-cap pile axial reactions for arbitrary pile coordinates (§1.2, §9-D5):

`R_i = N/n + Mx*y_i / Sum(y^2) + My*x_i / Sum(x^2)`

(plane-sections / rigid-cap assumption, EC2 §9.8.1 pile-as-compression-member; textbook method, not
itself an EC2 clause). Generalises the sheet's `Case 1`..`Case 4` formula (`Footing check!Z/AA`),
which only holds for its four symmetric grids; this closed form holds for any coordinate set. A
direction with zero second moment (every pile on that axis) cannot resist a moment about the other
axis by differential axial force alone — its term is 0 rather than a division by zero, matching the
single-pile `Case 4` layout where both moments are structurally irrelevant to this formula."""
from .models import PilePos


def rigid_cap_axial(n_kN: float, mx_kNm: float, my_kNm: float, piles: tuple[PilePos, ...]) -> tuple[float, ...]:
    """Per-pile axial reaction (kN), same order as `piles`. O(n)."""
    count = len(piles)
    if count == 0:
        raise ValueError("rigid_cap_axial: at least one pile is required")
    sum_y2 = sum(pile.y_m**2 for pile in piles)
    sum_x2 = sum(pile.x_m**2 for pile in piles)
    share = n_kN / count
    return tuple(
        share
        + (mx_kNm * pile.y_m / sum_y2 if sum_y2 > 0 else 0.0)
        + (my_kNm * pile.x_m / sum_x2 if sum_x2 > 0 else 0.0)
        for pile in piles
    )
