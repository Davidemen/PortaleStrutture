"""Step (spec calc step 5, `Neve accumulo!H33`): drift-zone length ls, EN1991-1-3 Annex B.3."""
from typing import Final

from strutture.shared.numeric import clamp

LS_MIN_M: Final[float] = 5.0
LS_MAX_M: Final[float] = 15.0


def lunghezza_accumulo(h_m: float) -> float:
    """ls = 2h, clamped to [5, 15] m."""
    return clamp(2 * h_m, LS_MIN_M, LS_MAX_M)
