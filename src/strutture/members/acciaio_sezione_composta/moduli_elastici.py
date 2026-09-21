"""Elastic section moduli Wel = I / distance-to-extreme-fibre, one per side of each axis."""
from .elementi import Elemento


def _estremi(elementi: tuple[Elemento, ...]) -> tuple[float, float, float, float]:
    """(y_min, y_max, x_min, x_max) of the whole section's outer fibres.

    Disabled elements (area 0, e.g. a legacy plate slot with `b_mm=0`) do not physically exist
    and must not stretch the outer fibres."""
    attivi = tuple(e for e in elementi if e.area_mm2 > 0.0)
    y_min = min(e.y_mm - e.h_mm / 2.0 for e in attivi)
    y_max = max(e.y_mm + e.h_mm / 2.0 for e in attivi)
    x_min = min(e.x_mm - e.b_mm / 2.0 for e in attivi)
    x_max = max(e.x_mm + e.b_mm / 2.0 for e in attivi)
    return y_min, y_max, x_min, x_max


def wel_mm3(elementi: tuple[Elemento, ...], ix_mm4: float, iy_mm4: float,
            x_n_mm: float, y_n_mm: float) -> tuple[float, float, float, float]:
    """(Wel,x top, Wel,x bottom, Wel,y +x side, Wel,y -x side)."""
    y_min, y_max, x_min, x_max = _estremi(elementi)
    wel_x_alto = ix_mm4 / (y_max - y_n_mm)
    wel_x_basso = ix_mm4 / (y_n_mm - y_min)
    wel_y_destra = iy_mm4 / (x_max - x_n_mm)
    wel_y_sinistra = iy_mm4 / (x_n_mm - x_min)
    return wel_x_alto, wel_x_basso, wel_y_destra, wel_y_sinistra
