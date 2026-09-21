"""Second moments of area about the two centroidal axes (Steiner/parallel-axis theorem).

Axis convention (matching the sheet's O/P columns and its Wpl,x/Wpl,y labels): `x` is the
horizontal (strong) bending axis — normal stress varies with `y`, own-axis inertia uses `h^3`;
`y` is the vertical (weak) bending axis — normal stress varies with `x`, own-axis inertia uses
`b^3`. `shared.section_geometry.rect(b, h)` already returns `b*h^3/12`, so calling it with the
arguments swapped gives the weak-axis own inertia for free.
"""
from strutture.shared.section_geometry import rect

from .elementi import Elemento


def inerzia_propria_x_mm4(elemento: Elemento) -> float:
    """Own-axis inertia about the horizontal (strong) axis through the element's centroid.

    A disabled element (area 0, e.g. a legacy plate slot with `b_mm=0`) has no inertia."""
    if elemento.area_mm2 == 0.0:
        return 0.0
    return rect(elemento.b_mm, elemento.h_mm).inertia_mm4


def inerzia_propria_y_mm4(elemento: Elemento) -> float:
    """Own-axis inertia about the vertical (weak) axis through the element's centroid."""
    if elemento.area_mm2 == 0.0:
        return 0.0
    return rect(elemento.h_mm, elemento.b_mm).inertia_mm4


def contributo_ix_mm4(elemento: Elemento, y_n_mm: float) -> float:
    return inerzia_propria_x_mm4(elemento) + elemento.area_mm2 * (elemento.y_mm - y_n_mm) ** 2


def contributo_iy_mm4(elemento: Elemento, x_n_mm: float) -> float:
    return inerzia_propria_y_mm4(elemento) + elemento.area_mm2 * (elemento.x_mm - x_n_mm) ** 2


def inerzia_sezione_mm4(elementi: tuple[Elemento, ...], x_n_mm: float, y_n_mm: float) -> tuple[float, float]:
    """(Ix, Iy) of the whole composite section about its own centroid."""
    ix = sum(contributo_ix_mm4(e, y_n_mm) for e in elementi)
    iy = sum(contributo_iy_mm4(e, x_n_mm) for e in elementi)
    return ix, iy
