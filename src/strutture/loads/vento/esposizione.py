"""Step (spec §4.9-10): exposure coefficient ce(z), §3.3.7. Shared by the scalar ce(H) (Vento!H37) and
every row of the pressure profile (Tabelle!O-column, which stores sqrt(ce) but resolves to the same
quantity once squared back into the pressure formula qz=qb*ce -- see spec §8).
"""
import math


def coefficiente_esposizione(z_m: float, kr: float, z0: float, zmin: float, ct: float) -> float:
    """ce(z) = kr^2*ct*ln(z_eff/z0)*(7+ct*ln(z_eff/z0)), with z_eff=max(z, zmin) (§3.3.7): the
    exposure coefficient is constant below zmin and follows the log-law from zmin upward.
    """
    z_eff = max(z_m, zmin)
    log_term = ct * math.log(z_eff / z0)
    return kr**2 * log_term * (7 + log_term)
