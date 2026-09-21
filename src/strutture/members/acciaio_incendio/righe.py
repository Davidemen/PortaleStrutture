"""resistenza!B9:H32 — one row per exposure time t."""
from strutture.shared.fire_reduction import gas_temperature_C, reduction_factors

from .models import MaterialeBase, RigaResistenzaIncendio


def riga_resistenza_incendio(t_min: float, materiale: MaterialeBase, e_20_MPa: float) -> RigaResistenzaIncendio:
    """One (t, θ, ky, kE, fy,θ, fu,θ, Eθ) row. fu,θ reuses ky,θ (fire code doesn't tabulate a
    separate fu reduction — spec §7, standard practice, not a bug)."""
    theta_C = gas_temperature_C(t_min)
    factors = reduction_factors(theta_C)
    return RigaResistenzaIncendio(
        t_min=t_min,
        theta_C=theta_C,
        ky_theta=factors.ky_theta,
        kE_theta=factors.kE_theta,
        fy_theta_MPa=materiale.fy_20_MPa * factors.ky_theta,
        fu_theta_MPa=materiale.fu_20_MPa * factors.ky_theta,
        e_theta_MPa=e_20_MPa * factors.kE_theta,
    )
