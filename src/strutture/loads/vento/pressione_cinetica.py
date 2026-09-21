"""Step (spec §4.8): reference kinetic pressure qb, Vento!H36, §3.3.6."""
from .costanti import AIR_DENSITY_KG_M3, PA_TO_KN_M2


def pressione_cinetica_riferimento(vr_ms: float) -> float:
    """qb = 0.5*rho*vR^2 / 1000 [kN/m2] (§3.3.6)."""
    return 0.5 * AIR_DENSITY_KG_M3 * vr_ms**2 / PA_TO_KN_M2
