"""EN 1992-1-1 §6.2.2 eq. 6.2.a (beam shear without reinforcement) and §6.4.4 eq. 6.47
(punching, with the 2d/a enhancement inside the 2d perimeter, §6.4.4(2))."""
from strutture.shared.numeric import clamp

from .models import VRdC
from .v_min import V_MIN_COEFFICIENT_EN, v_min

C_RD_C_COEFFICIENT_EN = 0.18  # EN default: CRd,c = 0.18/gamma_c; NA may replace 0.18.
K1_EN = 0.15  # EN default axial-stress coefficient k1 (§6.2.2(1)).
RHO_L_MAX = 0.02  # EC2 §6.2.2(1)/§6.4.4(1): rho_l used in the formula is capped at 2%.


def v_rd_c(
    k: float,
    rho: float,
    fck_MPa: float,
    sigma_cp_MPa: float,
    gamma_c: float = 1.5,
    *,
    c_rd_c_coefficient: float = C_RD_C_COEFFICIENT_EN,
    k1: float = K1_EN,
    v_min_coefficient: float = V_MIN_COEFFICIENT_EN,
    av_over_2d: float | None = None,
) -> VRdC:
    """Concrete-only shear/punching resistance.

    Without `av_over_2d`: vRd,c = max(CRd,c*k*(100*rho*fck)^(1/3), vmin) + k1*sigma_cp (§6.2.2 eq. 6.2.a).
    With `av_over_2d` (= 2d/a, only meaningful for a <= 2d): vRd = max(concrete_term, vmin)*2d/a + k1*sigma_cp
    (§6.4.4(2) eq. 6.50) — the vmin floor is enhanced by the same 2d/a factor rather than dropped, and
    sigma_cp (for prestressed/axially-loaded slabs) is still added.
    """
    if fck_MPa <= 0:
        raise ValueError(f"fck_MPa must be positive, got {fck_MPa}")
    if gamma_c <= 0:
        raise ValueError(f"gamma_c must be positive, got {gamma_c}")
    if rho < 0:
        raise ValueError(f"rho must be non-negative, got {rho}")

    rho_capped = clamp(rho, 0.0, RHO_L_MAX)
    c_rd_c = c_rd_c_coefficient / gamma_c
    concrete_term = c_rd_c * k * (100.0 * rho_capped * fck_MPa) ** (1.0 / 3.0)

    v_min_MPa = v_min(k, fck_MPa, coefficient=v_min_coefficient)
    k1_sigma_cp = k1 * sigma_cp_MPa

    if av_over_2d is not None:
        return VRdC(
            v_rd_c_MPa=max(concrete_term, v_min_MPa) * av_over_2d + k1_sigma_cp,
            concrete_term_MPa=concrete_term,
            v_min_MPa=v_min_MPa,
            k1_sigma_cp_MPa=k1_sigma_cp,
            enhancement_factor=av_over_2d,
        )

    return VRdC(
        v_rd_c_MPa=max(concrete_term, v_min_MPa) + k1_sigma_cp,
        concrete_term_MPa=concrete_term,
        v_min_MPa=v_min_MPa,
        k1_sigma_cp_MPa=k1_sigma_cp,
        enhancement_factor=None,
    )
