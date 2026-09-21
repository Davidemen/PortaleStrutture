"""Pile coordinates from `schema_pali` + spacings (uniform rectangular grid, centred on the group
centroid — the only layout the sheet's `Case 1`..`Case 4` selector supports, §9-D5)."""
from .models import PilePos, SchemaPali

_GRID_COUNTS: dict[SchemaPali, tuple[int, int]] = {
    "2x2": (2, 2),
    "2x1": (2, 1),
    "1x2": (1, 2),
    "1x1": (1, 1),
}


def pile_coordinates(schema_pali: SchemaPali, spacing_x_m: float, spacing_y_m: float) -> tuple[PilePos, ...]:
    """Piles on a `count_x` x `count_y` grid, spaced `spacing_x_m`/`spacing_y_m`, centred at (0, 0)."""
    count_x, count_y = _GRID_COUNTS[schema_pali]
    xs = _centred_positions(count_x, spacing_x_m)
    ys = _centred_positions(count_y, spacing_y_m)
    return tuple(PilePos(x_m=x, y_m=y) for y in ys for x in xs)


def _centred_positions(count: int, spacing: float) -> tuple[float, ...]:
    """`count` positions spaced `spacing` apart, centred on 0 (single pile -> [0.0])."""
    if count < 1:
        raise ValueError(f"pile grid count must be >= 1, got {count}")
    span = spacing * (count - 1)
    return tuple(-span / 2 + i * spacing for i in range(count))
