"""Pure polygon geometry for the RC section engine: tuples of `(x_mm, y_mm)` in, tuples out, no
numpy, no mutation. Vertices are counter-clockwise (CCW) simple polygons (possibly non-convex:
T, L, U, wall-with-boundary-elements outlines are all supported). Angles in radians.

Formulas follow the standard polygon shoelace / inertia identities (e.g. Paul Bourke, "Polygon
Area and Centroid"): for consecutive vertices `(x_i, y_i)`, `(x_{i+1}, y_{i+1})` (wrapping around),
`cross_i = x_i*y_{i+1} - x_{i+1}*y_i`.
"""
from math import cos, hypot, sin

Punto = tuple[float, float]
Poligono = tuple[Punto, ...]


def _cross(p: Punto, q: Punto) -> float:
    return p[0] * q[1] - q[0] * p[1]


def area_con_segno(poligono: Poligono) -> float:
    """Signed shoelace area: positive when `poligono` is CCW, negative when CW."""
    n = len(poligono)
    return 0.5 * sum(_cross(poligono[i], poligono[(i + 1) % n]) for i in range(n))


def area(poligono: Poligono) -> float:
    """Unsigned area (mm²)."""
    return abs(area_con_segno(poligono))


def antiorario(poligono: Poligono) -> bool:
    """True if `poligono` winds counter-clockwise."""
    return area_con_segno(poligono) > 0.0


def normalizza_antiorario(poligono: Poligono) -> Poligono:
    """Reverse vertex order if `poligono` winds clockwise, so the result is always CCW."""
    return poligono if antiorario(poligono) else tuple(reversed(poligono))


def area_e_centroide(poligono: Poligono) -> tuple[float, float, float]:
    """`(area_con_segno, cx, cy)` in one shoelace pass — used on every integration strip."""
    n = len(poligono)
    a6 = 0.0
    cx = 0.0
    cy = 0.0
    for i in range(n):
        x0, y0 = poligono[i]
        x1, y1 = poligono[(i + 1) % n]
        cr = x0 * y1 - x1 * y0
        a6 += cr
        cx += (x0 + x1) * cr
        cy += (y0 + y1) * cr
    a_con_segno = a6 / 2.0
    if a6 == 0.0:
        return 0.0, 0.0, 0.0
    return a_con_segno, cx / (3.0 * a6), cy / (3.0 * a6)


def centroide(poligono: Poligono) -> Punto:
    _, cx, cy = area_e_centroide(poligono)
    return cx, cy


def momenti_secondo_ordine(poligono: Poligono) -> tuple[float, float, float]:
    """`(Ixx, Iyy, Ixy)` about the ORIGIN of the given coordinates (mm⁴), always positive-area
    convention regardless of winding (uses the unsigned area sign correction)."""
    n = len(poligono)
    ixx = iyy = ixy = 0.0
    for i in range(n):
        x0, y0 = poligono[i]
        x1, y1 = poligono[(i + 1) % n]
        cr = x0 * y1 - x1 * y0
        ixx += (y0 * y0 + y0 * y1 + y1 * y1) * cr
        iyy += (x0 * x0 + x0 * x1 + x1 * x1) * cr
        ixy += (x0 * y1 + 2.0 * x0 * y0 + 2.0 * x1 * y1 + x1 * y0) * cr
    return ixx / 12.0, iyy / 12.0, ixy / 24.0


def momenti_centroidali(poligono: Poligono) -> tuple[float, float, float]:
    """`(Ixx, Iyy, Ixy)` about the polygon's own centroid (parallel-axis theorem)."""
    a_con_segno, cx, cy = area_e_centroide(poligono)
    ixx0, iyy0, ixy0 = momenti_secondo_ordine(poligono)
    return (
        ixx0 - a_con_segno * cy * cy,
        iyy0 - a_con_segno * cx * cx,
        ixy0 - a_con_segno * cx * cy,
    )


def bounding_box(poligono: Poligono) -> tuple[float, float, float, float]:
    """`(xmin, ymin, xmax, ymax)`."""
    xs = [p[0] for p in poligono]
    ys = [p[1] for p in poligono]
    return min(xs), min(ys), max(xs), max(ys)


def _distanza_punto_segmento(px: float, py: float, x0: float, y0: float, x1: float, y1: float) -> float:
    dx, dy = x1 - x0, y1 - y0
    lung2 = dx * dx + dy * dy
    if lung2 == 0.0:
        return hypot(px - x0, py - y0)
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / lung2))
    return hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def punto_in_poligono(punto: Punto, poligono: Poligono, tolleranza_mm: float = 0.0) -> bool:
    """Point-in-polygon (ray casting, works for non-convex outlines); a point within
    `tolleranza_mm` of an edge counts as inside."""
    px, py = punto
    n = len(poligono)
    for i in range(n):
        x0, y0 = poligono[i]
        x1, y1 = poligono[(i + 1) % n]
        if _distanza_punto_segmento(px, py, x0, y0, x1, y1) <= tolleranza_mm:
            return True
    dentro = False
    for i in range(n):
        x0, y0 = poligono[i]
        x1, y1 = poligono[(i + 1) % n]
        if (y0 > py) != (y1 > py):
            x_int = x0 + (py - y0) * (x1 - x0) / (y1 - y0)
            if px < x_int:
                dentro = not dentro
    return dentro


def _orientamento(p: Punto, q: Punto, r: Punto) -> float:
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])


def _sul_segmento(p: Punto, q: Punto, r: Punto) -> bool:
    return min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])


def _segmenti_si_intersecano(a0: Punto, a1: Punto, b0: Punto, b1: Punto) -> bool:
    o1, o2 = _orientamento(a0, a1, b0), _orientamento(a0, a1, b1)
    o3, o4 = _orientamento(b0, b1, a0), _orientamento(b0, b1, a1)
    if (o1 > 0) != (o2 > 0) and o1 != 0 and o2 != 0 and (o3 > 0) != (o4 > 0) and o3 != 0 and o4 != 0:
        return True
    if o1 == 0 and _sul_segmento(a0, b0, a1):
        return True
    if o2 == 0 and _sul_segmento(a0, b1, a1):
        return True
    if o3 == 0 and _sul_segmento(b0, a0, b1):
        return True
    return o4 == 0 and _sul_segmento(b0, a1, b1)


def poligono_semplice(poligono: Poligono) -> bool:
    """True if no two non-adjacent edges of `poligono` intersect (self-intersection check)."""
    n = len(poligono)
    if n < 3:
        return False
    lati = [(poligono[i], poligono[(i + 1) % n]) for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            adiacenti = j == i + 1 or (i == 0 and j == n - 1)
            if adiacenti:
                continue
            if _segmenti_si_intersecano(*lati[i], *lati[j]):
                return False
    return True


def trasla(poligono: Poligono, dx: float, dy: float) -> Poligono:
    return tuple((x + dx, y + dy) for x, y in poligono)


def ruota(poligono: Poligono, angolo_rad: float, centro: Punto = (0.0, 0.0)) -> Poligono:
    """Rotate CCW by `angolo_rad` about `centro`."""
    cx, cy = centro
    ca, sa = cos(angolo_rad), sin(angolo_rad)
    risultato = []
    for x, y in poligono:
        dx, dy = x - cx, y - cy
        risultato.append((cx + dx * ca - dy * sa, cy + dx * sa + dy * ca))
    return tuple(risultato)


def _interseca_retta(p: Punto, q: Punto, a: float, b: float, c: float, val_p: float, val_q: float) -> Punto:
    t = val_p / (val_p - val_q)
    return p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])


def taglia_semipiano(poligono: Poligono, a: float, b: float, c: float) -> Poligono:
    """Sutherland–Hodgman clip: keep the part of `poligono` where `a*x + b*y + c <= 0`. Correct
    for any simple subject polygon (convex or not) since the clip window here is a single
    half-plane; strip integration clips twice (two parallel half-planes) to cut a band."""
    n = len(poligono)
    if n == 0:
        return ()
    uscita: list[Punto] = []
    for i in range(n):
        corrente = poligono[i]
        precedente = poligono[i - 1]
        val_c = a * corrente[0] + b * corrente[1] + c
        val_p = a * precedente[0] + b * precedente[1] + c
        corrente_dentro = val_c <= 0.0
        precedente_dentro = val_p <= 0.0
        if corrente_dentro != precedente_dentro:
            uscita.append(_interseca_retta(precedente, corrente, a, b, c, val_p, val_c))
        if corrente_dentro:
            uscita.append(corrente)
    return tuple(uscita)
