"""Step 3 (spec §4.3): cpe windward face, cells D13/E13. Circ. C3.3.8.1."""

WINDWARD_SLENDER_LIMIT = 5.0  # h/d>5: not defined by the rectangular-plan table ("ND")
WINDWARD_BREAKPOINT = 1.0
WINDWARD_BASE = 0.7
WINDWARD_SLOPE = 0.1
WINDWARD_CAP = 0.8


def cpe_windward(hd: float) -> float | None:
    """Windward cpe: linear 0.7->0.8 for h/d in [0,1], capped at 0.8 up to h/d=5, None ("ND") above."""
    if hd > WINDWARD_SLENDER_LIMIT:
        return None
    if hd <= WINDWARD_BREAKPOINT:
        return WINDWARD_BASE + WINDWARD_SLOPE * hd
    return WINDWARD_CAP
