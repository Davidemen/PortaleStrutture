"""Exact biaxial Navier contact pressure, valid while the resultant stays inside the kern (no
uplift anywhere on the bx_m * by_m footing): sigma(x, y) = N/A * (1 + 12*ex*x/bx^2 + 12*ey*y/by^2),
the linear superposition of the two uniaxial terms (exact here because the plane never goes
negative, so no clipping is needed).
"""
from .models import BiaxialPressure

# Corner order matches models.BiaxialPressure.corners_kpa and polygon.rectangle: (-x,-y) (+x,-y) (+x,+y) (-x,+y).
_CORNER_SIGNS: tuple[tuple[float, float], ...] = ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0))


def biaxial_navier(n_kn: float, ex_m: float, ey_m: float, bx_m: float, by_m: float,
                    metodo: str = "esatto") -> BiaxialPressure:
    """Corner pressures + extremes for a fully-compressed (in-kern) rectangular footing."""
    sigma_uniform_kpa = n_kn / (bx_m * by_m)
    sigma_a, sigma_b, sigma_c, sigma_d = (
        sigma_uniform_kpa * (1.0 + 6.0 * ex_m * sx / bx_m + 6.0 * ey_m * sy / by_m) for sx, sy in _CORNER_SIGNS
    )
    corners_kpa = (sigma_a, sigma_b, sigma_c, sigma_d)
    return BiaxialPressure(
        metodo=metodo, ex_m=ex_m, ey_m=ey_m, in_kern=True,
        sigma_max_kpa=max(corners_kpa), sigma_min_kpa=min(corners_kpa), compressed_ratio=1.0,
        corners_kpa=corners_kpa, neutral_axis=None,
    )
