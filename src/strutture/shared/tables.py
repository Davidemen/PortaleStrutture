"""Lookup engine replacing VLOOKUP/HLOOKUP. Tables are immutable tuples of (key, row) pairs."""
from collections.abc import Sequence
from itertools import pairwise

from .numeric import lerp


class KeyNotFound(KeyError):
    """Raised instead of Excel's #N/A."""


def exact_lookup[K, V](table: Sequence[tuple[K, V]], key: K, *, ignore_case: bool = True) -> V:
    """VLOOKUP(..., FALSE). Excel compares text case-insensitively, so that is the default."""
    def norm(k: object) -> object:
        return k.casefold() if ignore_case and isinstance(k, str) else k

    for candidate, row in table:
        if norm(candidate) == norm(key):
            return row
    raise KeyNotFound(f"{key!r} not in table (known keys: {[k for k, _ in table][:12]})")


def band_lookup[V](table: Sequence[tuple[float, V]], x: float) -> V:
    """VLOOKUP(..., TRUE): row of the largest key <= x. Keys must be ascending."""
    matches = [row for key, row in table if key <= x]
    if not matches:
        raise KeyNotFound(f"{x} is below the first band {table[0][0] if table else '∅'}")
    return matches[-1]


def interp_lookup(table: Sequence[tuple[float, float]], x: float) -> float:
    """Piecewise-linear interpolation over ascending (x, y) points; no extrapolation."""
    if not table or not table[0][0] <= x <= table[-1][0]:
        raise KeyNotFound(f"{x} outside table range")
    for (x0, y0), (x1, y1) in pairwise(table):
        if x0 <= x <= x1:
            return lerp(x, x0, y0, x1, y1)
    return table[-1][1]
