"""EN 1992-1-1 §6.5.2(1) strut design compressive stress limit: fcd for struts with no transverse tension,
0.6*ν'*fcd for struts crossed by transverse tension (typical of pile-cap diagonal struts)."""
from .models import StrutResistance
from .nu_prime import nu_prime

CRACKED_COEFFICIENT_EN = 0.6  # EN default in sigma_Rd,max = 0.6 * nu' * fcd for cracked struts.


def strut_capacity(
    fck_MPa: float,
    gamma_c: float = 1.5,
    *,
    alpha_cc: float = 1.0,
    cracked: bool = True,
    cracked_coefficient: float = CRACKED_COEFFICIENT_EN,
    area_mm2: float | None = None,
) -> StrutResistance:
    """sigma_Rd,max = fcd (uncracked) or cracked_coefficient*nu'*fcd (cracked, transverse tension present).
    When `area_mm2` is given, also returns the design resistance as a force `fns_kN`."""
    if gamma_c <= 0:
        raise ValueError(f"gamma_c must be positive, got {gamma_c}")
    if area_mm2 is not None and area_mm2 <= 0:
        raise ValueError(f"area_mm2 must be positive, got {area_mm2}")

    nu = nu_prime(fck_MPa)
    fcd_MPa = alpha_cc * fck_MPa / gamma_c
    sigma_rd_max_MPa = cracked_coefficient * nu * fcd_MPa if cracked else fcd_MPa
    fns_kN = sigma_rd_max_MPa * area_mm2 / 1000.0 if area_mm2 is not None else None
    return StrutResistance(
        sigma_rd_max_MPa=sigma_rd_max_MPa, nu_prime=nu, fcd_MPa=fcd_MPa, cracked=cracked, fns_kN=fns_kN
    )
