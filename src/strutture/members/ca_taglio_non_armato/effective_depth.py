"""Effective depth (sheet B10)."""


def effective_depth_mm(h_mm: float, c_mm: float) -> float:
    """d = h - c, mm."""
    return h_mm - c_mm
