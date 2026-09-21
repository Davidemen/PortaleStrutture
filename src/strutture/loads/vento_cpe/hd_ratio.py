"""Step 1 (spec §4.1): slenderness ratio h/d, cells D9/E9."""


def hd_ratio(h: float, d: float) -> float:
    """Ratio of building height to plan depth for one wind direction."""
    return h / d
