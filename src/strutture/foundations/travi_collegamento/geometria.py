"""Rectangular-section geometry helpers shared by the NTC and EN slenderness/stirrup steps
(sheets `C41`/`C39` and `C51`/`C60`)."""
import math


def raggio_inerzia_debole_mm(b_mm: float, h_mm: float) -> float:
    """Radius of gyration about the weak axis of a b x h rectangle, `i = sqrt(min³·max/12 / (b·h))`."""
    lato_min, lato_max = min(b_mm, h_mm), max(b_mm, h_mm)
    return math.sqrt((lato_min**3 * lato_max / 12.0) / (b_mm * h_mm))


def altezza_utile_mm(h_mm: float, copriferro_mm: float) -> float:
    """Effective depth d = H - cf."""
    return h_mm - copriferro_mm
