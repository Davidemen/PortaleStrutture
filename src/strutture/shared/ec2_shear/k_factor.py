"""EN 1992-1-1 §6.2.2(1) size-effect factor k, capped at 2.0 (bug source when left unclamped: see
architecture-batch2.md §7 `plinti-pali AR99`)."""


def k_size(d_mm: float) -> float:
    """k = min(1 + sqrt(200/d), 2.0), d in mm. Raises ValueError for non-positive depth."""
    if d_mm <= 0:
        raise ValueError(f"d_mm must be positive, got {d_mm}")
    return min(1.0 + (200.0 / d_mm) ** 0.5, 2.0)
