"""Step 5 (spec §4.5): cpe leeward face, cells D15/E15. Circ. C3.3.8.1."""

LEEWARD_SLENDER_LIMIT = 5.0
LEEWARD_BREAKPOINT = 1.0
LEEWARD_BASE = -0.3
LEEWARD_SLOPE = -0.2
LEEWARD_BASE_2 = -0.5
LEEWARD_SLOPE_2 = -0.05


def cpe_leeward(hd: float) -> float | None:
    """Leeward cpe: two linear segments (breakpoint h/d=1), None ("ND") above h/d=5."""
    if hd > LEEWARD_SLENDER_LIMIT:
        return None
    if hd <= LEEWARD_BREAKPOINT:
        return LEEWARD_BASE + LEEWARD_SLOPE * hd
    return LEEWARD_BASE_2 + LEEWARD_SLOPE_2 * (hd - LEEWARD_BREAKPOINT)
