"""Step 4 (spec §4.4): cpe side faces, cells D14/E14. Circ. C3.3.8.1."""

SIDE_SLENDER_LIMIT = 5.0
SIDE_BREAKPOINT = 0.5
SIDE_BASE = -0.5
SIDE_SLOPE = -0.8
SIDE_CAP = -0.9


def cpe_side(hd: float) -> float | None:
    """Side-wall cpe: linear -0.5->-0.9 for h/d in [0,0.5], capped at -0.9 up to h/d=5, None ("ND") above."""
    if hd > SIDE_SLENDER_LIMIT:
        return None
    if hd <= SIDE_BREAKPOINT:
        return SIDE_BASE + SIDE_SLOPE * hd
    return SIDE_CAP
