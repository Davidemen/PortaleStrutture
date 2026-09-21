"""Area and centroid of the composite section (weighted average of the element centroids).

`legacy_compat=True` reproduces the sheet's H6 bug: the yN weighted-average formula
`=(D6*F6+D7*F7+D8*F8+D9*F9+D10*E10)/SUM(D6:D10)` uses the LAST element's x-coordinate (E10)
instead of its y-coordinate (F10). Numerically harmless while that last element's area is zero
(the golden case), but wrong whenever it is populated — see docs/divergences.
"""
from .elementi import Elemento


def area_totale_mm2(elementi: tuple[Elemento, ...]) -> float:
    return sum(e.area_mm2 for e in elementi)


def baricentro(elementi: tuple[Elemento, ...], *, legacy_compat: bool) -> tuple[float, float]:
    """(xN, yN) of the composite section."""
    area = area_totale_mm2(elementi)
    if area <= 0.0:
        raise ValueError("area totale della sezione nulla: nessun elemento con area positiva")
    x_n = sum(e.area_mm2 * e.x_mm for e in elementi) / area
    if legacy_compat and elementi:
        *precedenti, ultimo = elementi
        y_n = (sum(e.area_mm2 * e.y_mm for e in precedenti) + ultimo.area_mm2 * ultimo.x_mm) / area
    else:
        y_n = sum(e.area_mm2 * e.y_mm for e in elementi) / area
    return x_n, y_n
