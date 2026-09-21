"""EN 1992-1-1 §6.4.5(1) eq. 6.52, effective design yield strength of punching shear reinforcement.
Fixes architecture-batch2.md §7 `punzonamento H56`: the source sheet computes 250+0.25d uncapped."""

FYWD_EF_BASE_MPA = 250.0
FYWD_EF_SLOPE = 0.25


def fywd_ef(d_mm: float, fywd_MPa: float) -> float:
    """fywd,ef = min(250 + 0.25*d, fywd), d in mm."""
    if d_mm <= 0:
        raise ValueError(f"d_mm must be positive, got {d_mm}")
    if fywd_MPa <= 0:
        raise ValueError(f"fywd_MPa must be positive, got {fywd_MPa}")
    return min(FYWD_EF_BASE_MPA + FYWD_EF_SLOPE * d_mm, fywd_MPa)
