"""No-tension plane-pressure solver for a rigid rectangular footing outside its biaxial kern.

The exact no-tension solution is a pressure plane sigma(x, y) = k*(n.(x,y) - d), clipped to >= 0
(n = (cos theta, sin theta)), whose resultant over the bx*by footing equals (N, N*ex, N*ey). This
plane has exactly 3 degrees of freedom (theta, d, k); k is eliminated in closed form from the
force equation (`_resultant` below always returns a resultant whose total force is exactly N),
leaving a 2-unknown (theta, d) root-finding problem in the two moment equations — solved by a
damped 2-D Newton fixed-point iteration on the compressed polygon (docs/architecture-batch2.md
§8-D2), started at the direction of (ex_m, ey_m) which is exact whenever bx_m == by_m (square
footing) and an excellent first guess otherwise.
"""
import math
from typing import NamedTuple

from .models import NeutralAxis
from .polygon import Polygon, clip_half_plane, first_moments, rectangle, second_moments, support
from .polygon import area as polygon_area

_MAX_ITERATIONS = 60
_TOL = 1e-10
_FD_ANGLE_STEP = 1e-6  # rad, for the finite-difference Jacobian
_RELATIVE_OFFSET_MARGIN = 1e-9  # keeps d strictly inside (-h, h): a non-degenerate compressed polygon
_MAX_ANGLE_STEP = 0.5  # rad per iteration, damping against Newton overshoot near degenerate polygons
_MAX_OFFSET_STEP_FRACTION = 0.4  # fraction of the current support h(n), same purpose for the offset step


class NoTensionSolution(NamedTuple):
    sigma_max_kpa: float
    compressed_ratio: float
    corners_kpa: tuple[float, float, float, float]
    neutral_axis: NeutralAxis


def _resultant(nx: float, ny: float, d: float, rect: Polygon, n_kn: float) -> tuple[float, float]:
    """(ex_computed, ey_computed) of the pressure plane sigma = k*(n.p - d) clipped to the
    compressed side, with k fixed so that the total compressed force is exactly n_kn.
    """
    polygon = clip_half_plane(rect, nx, ny, d)
    area_m2 = polygon_area(polygon)
    mx1, my1 = first_moments(polygon)
    denom = (nx * mx1 + ny * my1) - d * area_m2
    if len(polygon) < 3 or denom <= 0 or area_m2 <= 0:
        raise _DegeneratePolygon
    sxx, syy, sxy = second_moments(polygon)
    k_kpa_m = n_kn / denom
    ex_computed = k_kpa_m * ((nx * sxx + ny * sxy) - d * mx1) / n_kn
    ey_computed = k_kpa_m * ((nx * sxy + ny * syy) - d * my1) / n_kn
    return ex_computed, ey_computed


class _DegeneratePolygon(Exception):
    """Raised internally when (theta, d) clips away the whole footing (used to reject bad Newton
    steps and fall back to a smaller one)."""


def _clamp_offset(theta: float, d: float, bx_m: float, by_m: float) -> float:
    h = support(math.cos(theta), math.sin(theta), bx_m, by_m)
    margin = h * _RELATIVE_OFFSET_MARGIN
    return min(max(d, -h + margin), h - margin)


def _residual(theta: float, d: float, rect: Polygon, n_kn: float, ex_m: float, ey_m: float) -> tuple[float, float]:
    ex_c, ey_c = _resultant(math.cos(theta), math.sin(theta), d, rect, n_kn)
    return ex_c - ex_m, ey_c - ey_m


def _newton_step(theta: float, d: float, rect: Polygon, bx_m: float, by_m: float, n_kn: float, ex_m: float,
                  ey_m: float) -> tuple[float, float]:
    """One damped Newton update of (theta, d) towards zeroing `_residual`, via a central-difference
    Jacobian. Falls back to a halved step (both here and by the caller) if a probe point clips away
    the whole footing.
    """
    d_step = max(bx_m, by_m) * 1e-6
    fx0, fy0 = _residual(theta, d, rect, n_kn, ex_m, ey_m)
    fx_tp, fy_tp = _residual(theta + _FD_ANGLE_STEP, d, rect, n_kn, ex_m, ey_m)
    fx_tm, fy_tm = _residual(theta - _FD_ANGLE_STEP, d, rect, n_kn, ex_m, ey_m)
    fx_dp, fy_dp = _residual(theta, _clamp_offset(theta, d + d_step, bx_m, by_m), rect, n_kn, ex_m, ey_m)
    fx_dm, fy_dm = _residual(theta, _clamp_offset(theta, d - d_step, bx_m, by_m), rect, n_kn, ex_m, ey_m)

    j11, j12 = (fx_tp - fx_tm) / (2.0 * _FD_ANGLE_STEP), (fx_dp - fx_dm) / (2.0 * d_step)
    j21, j22 = (fy_tp - fy_tm) / (2.0 * _FD_ANGLE_STEP), (fy_dp - fy_dm) / (2.0 * d_step)
    det = j11 * j22 - j12 * j21
    if det == 0:
        raise _DegeneratePolygon
    dtheta = (-fx0 * j22 + fy0 * j12) / det
    dd = (-j11 * fy0 + j21 * fx0) / det
    new_theta = theta + max(-_MAX_ANGLE_STEP, min(_MAX_ANGLE_STEP, dtheta))
    max_dd = _MAX_OFFSET_STEP_FRACTION * support(math.cos(new_theta), math.sin(new_theta), bx_m, by_m)
    return new_theta, _clamp_offset(new_theta, d + max(-max_dd, min(max_dd, dd)), bx_m, by_m)


def biaxial_no_tension(n_kn: float, ex_m: float, ey_m: float, bx_m: float, by_m: float) -> NoTensionSolution:
    """Solve the no-tension plane for target eccentricities (ex_m, ey_m) outside the kern.

    sigma_min is always 0 in this branch (there is uplift somewhere on the footing by definition).
    """
    rect = rectangle(bx_m, by_m)
    theta = math.atan2(ey_m, ex_m)
    d = _clamp_offset(theta, 0.0, bx_m, by_m)
    for _ in range(_MAX_ITERATIONS):
        try:
            rx, ry = _residual(theta, d, rect, n_kn, ex_m, ey_m)
            if math.hypot(rx, ry) < _TOL * max(1.0, math.hypot(ex_m, ey_m)):
                break
            theta, d = _newton_step(theta, d, rect, bx_m, by_m, n_kn, ex_m, ey_m)
        except _DegeneratePolygon:
            d = _clamp_offset(theta, 0.5 * d, bx_m, by_m)  # retreat towards the centre and retry
    else:
        raise ValueError(f"biaxial_no_tension: did not converge for ex_m={ex_m}, ey_m={ey_m}")

    nx, ny = math.cos(theta), math.sin(theta)
    polygon = clip_half_plane(rect, nx, ny, d)
    area_m2 = polygon_area(polygon)
    mx1, my1 = first_moments(polygon)
    k_kpa_m = n_kn / ((nx * mx1 + ny * my1) - d * area_m2)

    corner_a, corner_b, corner_c, corner_d = (max(0.0, k_kpa_m * (nx * px + ny * py - d)) for px, py in rect)
    corners_kpa = (corner_a, corner_b, corner_c, corner_d)
    sigma_max_kpa = k_kpa_m * (support(nx, ny, bx_m, by_m) - d)
    neutral_axis = NeutralAxis(theta_rad=theta, offset_m=d, k_kpa_m=k_kpa_m)
    compressed_ratio = area_m2 / (bx_m * by_m)
    return NoTensionSolution(sigma_max_kpa=sigma_max_kpa, compressed_ratio=compressed_ratio,
                              corners_kpa=corners_kpa, neutral_axis=neutral_axis)
