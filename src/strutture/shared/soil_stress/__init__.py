"""Vertical stress increase under a uniformly loaded rectangle (docs/architecture-batch2.md §1.2):
Newmark/Steinbrenner corner integral, centre and arbitrary-point superposition, the oedometric
sheet's approximate 2:1 spread, and the Timoshenko-Goodier displacement-influence factor. Pure
functions, no I/O, no `Tool` registered — consumed by `strutture.geotechnics.cedimenti_*`."""
from .center import ic_center, under_center
from .models import PointStress
from .newmark import newmark_corner
from .point import under_point
from .spread import spread_2to1
from .steinbrenner import steinbrenner_is

__all__ = [
    "PointStress",
    "ic_center",
    "newmark_corner",
    "spread_2to1",
    "steinbrenner_is",
    "under_center",
    "under_point",
]
