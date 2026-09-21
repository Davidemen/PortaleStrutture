"""Closed-form contact pressure of a rigid footing under uniaxial bending.

Navier (sigma = N/A +- 6M/(b*l^2)) inside the kern; outside it, the classic no-tension
triangular-pressure closed form (contact length c = 3*(l/2 - |e|), sigma_max = 2N/(b*c)) — see
docs/specs/fond-plinti-isolati.md steps 8-9 (CHECKS!N..R): O = 3*(AX/2 - e) is exactly this c.
"""
from strutture.shared.report import CalcError

from .eccentricity import in_kern_uniaxial
from .models import UniaxialPressure


def uniaxial(n_kn: float, m_knm: float, b_m: float, l_m: float) -> UniaxialPressure:
    """Contact pressure of a b_m * l_m rigid footing under N (compression, kN) and a moment
    m_knm bending it along l_m (the eccentricity e = m_knm / n_kn acts along l_m; b_m is the
    other, unbent side). Raises CalcError if the resultant falls outside the footing (|e| >= l/2).
    """
    if n_kn <= 0:
        raise ValueError(f"n_kn must be > 0 (compression), got {n_kn}")
    if b_m <= 0 or l_m <= 0:
        raise ValueError(f"b_m and l_m must be > 0, got b_m={b_m}, l_m={l_m}")

    e_m = m_knm / n_kn
    if abs(e_m) >= l_m / 2.0:
        raise CalcError(
            f"La risultante (e={e_m:.4g} m) cade fuori dalla base del plinto (l/2={l_m / 2.0:.4g} m): "
            "geometria non verificabile.")

    area_m2 = b_m * l_m
    sigma_uniform_kpa = n_kn / area_m2
    if in_kern_uniaxial(e_m, l_m):
        delta_kpa = sigma_uniform_kpa * 6.0 * e_m / l_m
        sigma_a_kpa, sigma_b_kpa = sigma_uniform_kpa - delta_kpa, sigma_uniform_kpa + delta_kpa
        return UniaxialPressure(e_m=e_m, in_kern=True, sigma_max_kpa=max(sigma_a_kpa, sigma_b_kpa),
                                 sigma_min_kpa=min(sigma_a_kpa, sigma_b_kpa), contact_len_m=l_m)

    contact_len_m = 3.0 * (l_m / 2.0 - abs(e_m))
    sigma_max_kpa = 2.0 * n_kn / (b_m * contact_len_m)
    return UniaxialPressure(e_m=e_m, in_kern=False, sigma_max_kpa=sigma_max_kpa, sigma_min_kpa=0.0,
                             contact_len_m=contact_len_m)
