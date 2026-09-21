"""EN 1992-1-1 §6.2.2(1) eq. 6.3N, minimum shear resistance vmin (national-annex coefficient exposed)."""

V_MIN_COEFFICIENT_EN = 0.035  # EN default: vmin = 0.035 * k^1.5 * sqrt(fck); NA may replace it.


def v_min(k: float, fck_MPa: float, *, coefficient: float = V_MIN_COEFFICIENT_EN) -> float:
    """vmin = coefficient * k^1.5 * sqrt(fck). `coefficient` is the national-annex parameter (EN: 0.035)."""
    if fck_MPa <= 0:
        raise ValueError(f"fck_MPa must be positive, got {fck_MPa}")
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
    return coefficient * k**1.5 * fck_MPa**0.5
