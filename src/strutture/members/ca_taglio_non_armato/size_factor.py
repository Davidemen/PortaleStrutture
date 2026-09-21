"""Size-effect factor k (sheet B15)."""
from .tables import K_SIZE_FACTOR_MAX


def size_factor_k(d_mm: float) -> float:
    """k = MIN(1+sqrt(200/d), 2), d in mm."""
    raw = 1 + (200 / d_mm) ** 0.5
    return min(K_SIZE_FACTOR_MAX, raw)
