"""Generic 2-D polygon geometry: half-plane clipping and area/first/second moment integrals.

Pure geometry, no footing-specific knowledge — used by no_tension.py to integrate a linear
pressure field over the part of the rectangle that stays in compression.
"""
from collections.abc import Sequence

Point = tuple[float, float]
Polygon = tuple[Point, ...]


def clip_half_plane(polygon: Polygon, nx: float, ny: float, d: float) -> Polygon:
    """Sutherland-Hodgman clip of a convex `polygon` (vertices in order) to the closed half-plane
    {(x, y): nx*x + ny*y >= d}. Returns an empty tuple if nothing survives.
    """
    if not polygon:
        return ()
    out: list[Point] = []
    count = len(polygon)
    for i in range(count):
        curr = polygon[i]
        prev = polygon[i - 1]
        curr_val = nx * curr[0] + ny * curr[1] - d
        prev_val = nx * prev[0] + ny * prev[1] - d
        if curr_val >= 0:
            if prev_val < 0:
                out.append(_intersection(prev, curr, prev_val, curr_val))
            out.append(curr)
        elif prev_val >= 0:
            out.append(_intersection(prev, curr, prev_val, curr_val))
    return tuple(out)


def _intersection(prev: Point, curr: Point, prev_val: float, curr_val: float) -> Point:
    t = prev_val / (prev_val - curr_val)
    return (prev[0] + t * (curr[0] - prev[0]), prev[1] + t * (curr[1] - prev[1]))


def area(polygon: Polygon) -> float:
    return _shoelace(polygon) / 2.0


def first_moments(polygon: Polygon) -> tuple[float, float]:
    """(Mx, My) = (integral of x dA, integral of y dA) about the origin."""
    if len(polygon) < 3:
        return 0.0, 0.0
    mx = my = 0.0
    for (x0, y0), (x1, y1) in _edges(polygon):
        cross = x0 * y1 - x1 * y0
        mx += (x0 + x1) * cross
        my += (y0 + y1) * cross
    return mx / 6.0, my / 6.0


def second_moments(polygon: Polygon) -> tuple[float, float, float]:
    """(Sxx, Syy, Sxy) = (integral of x^2 dA, integral of y^2 dA, integral of x*y dA) about the
    origin, via the standard polygon second-moment formulas (Green's theorem).
    """
    if len(polygon) < 3:
        return 0.0, 0.0, 0.0
    sxx = syy = sxy = 0.0
    for (x0, y0), (x1, y1) in _edges(polygon):
        cross = x0 * y1 - x1 * y0
        sxx += (x0 * x0 + x0 * x1 + x1 * x1) * cross
        syy += (y0 * y0 + y0 * y1 + y1 * y1) * cross
        sxy += (x0 * y1 + 2.0 * x0 * y0 + 2.0 * x1 * y1 + x1 * y0) * cross
    return sxx / 12.0, syy / 12.0, sxy / 24.0


def _shoelace(polygon: Polygon) -> float:
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in _edges(polygon))


def _edges(polygon: Sequence[Point]) -> Sequence[tuple[Point, Point]]:
    count = len(polygon)
    return tuple((polygon[i], polygon[(i + 1) % count]) for i in range(count))


def rectangle(bx_m: float, by_m: float) -> Polygon:
    """Rectangle bx_m * by_m centred on the origin, vertices CCW starting at (-x,-y)."""
    hx, hy = bx_m / 2.0, by_m / 2.0
    return (-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)


def support(nx: float, ny: float, bx_m: float, by_m: float) -> float:
    """Support function of the bx_m * by_m rectangle in direction (nx, ny): max over the
    rectangle of n . p. Equals bx/2*|nx| + by/2*|ny| for an axis-aligned box centred at the origin.
    """
    return bx_m / 2.0 * abs(nx) + by_m / 2.0 * abs(ny)
