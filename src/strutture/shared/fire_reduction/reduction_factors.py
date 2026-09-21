"""Linear interpolation of EN1993-1-2 Table 3.1 at an arbitrary steel temperature θ."""
from strutture.shared.tables import interp_lookup

from .models import ReductionFactors
from .tables import TABLE_3_1

_KY_TABLE: tuple[tuple[float, float], ...] = tuple((theta, ky) for theta, ky, _, _ in TABLE_3_1)
_KP_TABLE: tuple[tuple[float, float], ...] = tuple((theta, kp) for theta, _, kp, _ in TABLE_3_1)
_KE_TABLE: tuple[tuple[float, float], ...] = tuple((theta, ke) for theta, _, _, ke in TABLE_3_1)


def reduction_factors(theta_C: float) -> ReductionFactors:
    """ky,θ / kp,θ / kE,θ at `theta_C`, piecewise-linear between Table 3.1's 100 °C brackets.
    Raises `strutture.shared.tables.KeyNotFound` outside [20, 1200] °C (table's own range)."""
    return ReductionFactors(
        theta_C=theta_C,
        ky_theta=interp_lookup(_KY_TABLE, theta_C),
        kp_theta=interp_lookup(_KP_TABLE, theta_C),
        kE_theta=interp_lookup(_KE_TABLE, theta_C),
    )
