"""Plastic section modulus about each axis.

Code-standard (`legacy_compat=False`): the true plastic neutral axis (PNA) by the equal-area
method — `shared.numeric.bisect` finds the axis position that splits the section into two areas
of A/2 each, then Wpl is the sum of the two half-areas' static moments about that axis. This
handles plates that straddle the axis (partial rectangle) generically.

Legacy (`legacy_compat=True`): the sheet's approximation, which never actually looks for the PNA
— it sums `A_i * |distance from the ELASTIC centroid|` (columns M/N), which is only exact when the
elastic and plastic centroids coincide (a doubly symmetric section with no added plates).
"""
from strutture.shared.numeric import bisect

from .elementi import Elemento

Striscia = tuple[float, float, float]  # (bordo_basso, bordo_alto, larghezza_trasversale)


def _strisce_asse_x(elementi: tuple[Elemento, ...]) -> tuple[Striscia, ...]:
    return tuple((e.y_mm - e.h_mm / 2.0, e.y_mm + e.h_mm / 2.0, e.b_mm) for e in elementi)


def _strisce_asse_y(elementi: tuple[Elemento, ...]) -> tuple[Striscia, ...]:
    return tuple((e.x_mm - e.b_mm / 2.0, e.x_mm + e.b_mm / 2.0, e.h_mm) for e in elementi)


def _area_sotto(strisce: tuple[Striscia, ...], soglia: float) -> float:
    totale = 0.0
    for basso, alto, larghezza in strisce:
        if soglia >= alto:
            totale += larghezza * (alto - basso)
        elif soglia > basso:
            totale += larghezza * (soglia - basso)
    return totale

def asse_neutro_plastico(strisce: tuple[Striscia, ...]) -> float:
    """Equal-area axis position (goal-seek replacing Excel: `bisect` on area_below(axis) = A/2)."""
    minimo = min(basso for basso, _, _ in strisce)
    massimo = max(alto for _, alto, _ in strisce)
    area_totale = sum(larghezza * (alto - basso) for basso, alto, larghezza in strisce)
    return bisect(lambda soglia: _area_sotto(strisce, soglia) - area_totale / 2.0, minimo, massimo)


def modulo_plastico_mm3(strisce: tuple[Striscia, ...], asse_neutro: float) -> float:
    """Wpl = sum of the static moments of the two half-areas about the equal-area axis."""
    momento = 0.0
    for basso, alto, larghezza in strisce:
        bordo_sopra = max(basso, asse_neutro)
        if alto > bordo_sopra:
            altezza, centro = alto - bordo_sopra, (alto + bordo_sopra) / 2.0
            momento += larghezza * altezza * abs(centro - asse_neutro)
        bordo_sotto = min(alto, asse_neutro)
        if bordo_sotto > basso:
            altezza, centro = bordo_sotto - basso, (bordo_sotto + basso) / 2.0
            momento += larghezza * altezza * abs(centro - asse_neutro)
    return momento


def wpl_x_mm3(elementi: tuple[Elemento, ...]) -> float:
    strisce = _strisce_asse_x(elementi)
    return modulo_plastico_mm3(strisce, asse_neutro_plastico(strisce))


def wpl_y_mm3(elementi: tuple[Elemento, ...]) -> float:
    strisce = _strisce_asse_y(elementi)
    return modulo_plastico_mm3(strisce, asse_neutro_plastico(strisce))


def wpl_x_legacy_mm3(elementi: tuple[Elemento, ...], y_n_mm: float) -> float:
    """Sheet's M-column sum: `SUM(A_i * |y_i - yN|)`."""
    return sum(e.area_mm2 * abs(e.y_mm - y_n_mm) for e in elementi)


def wpl_y_legacy_mm3(elementi: tuple[Elemento, ...], x_n_mm: float) -> float:
    """Sheet's N-column sum: `SUM(A_i * |x_i - xN|)`."""
    return sum(e.area_mm2 * abs(e.x_mm - x_n_mm) for e in elementi)
