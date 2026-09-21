"""Step (spec calc step 9, `Neve accumulo!H38`): sliding shape coeff μs from the taller roof."""
from typing import Final

SLIDE_ANGLE_THRESHOLD_DEG: Final[float] = 15.0  # EC1 Annex B.3: no sliding contribution below 15°


def mu_s(angle_deg: float, mu_sup: float) -> float:
    if angle_deg < SLIDE_ANGLE_THRESHOLD_DEG:
        return 0.0
    return mu_sup / 2
