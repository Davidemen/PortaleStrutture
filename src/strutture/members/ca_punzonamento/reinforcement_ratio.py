"""Spec step 9: geometric ratio of bonded tension reinforcement ρl (EC2§6.4.4(1)), combining the main
mat and an optional top-up layer per direction, then the geometric mean of both directions. The 2%
cap (EC2§6.4.4(1)) is applied later, inside `shared.ec2_shear.v_rd_c`, not here — this returns the raw
ratio so the >2% warning check can compare against the uncapped value, as the sheet's F35 cell does."""
from strutture.shared.rebar_catalog import bar_area

RHO_MAX_WARNING = 0.02  # EC2§6.4.4(1) — informational threshold, enforced downstream in v_rd_c


def _direction_ratio(phi_mm: float, passo_mm: float, phi_add_mm: float, passo_add_mm: float, d_mm: float) -> float:
    rho_principale = bar_area(phi_mm) / (passo_mm * d_mm)
    rho_aggiuntiva = 0.0 if passo_add_mm == 0 else bar_area(phi_add_mm) / (passo_add_mm * d_mm)
    return rho_principale + rho_aggiuntiva


def rho_l(px_mm: float, py_mm: float, phix_mm: float, phiy_mm: float, paddx_mm: float, paddy_mm: float,
          phiaddx_mm: float, phiaddy_mm: float, d_mm: float) -> float:
    """ρl = sqrt(ρx,tot * ρy,tot), uncapped."""
    rho_x = _direction_ratio(phix_mm, px_mm, phiaddx_mm, paddx_mm, d_mm)
    rho_y = _direction_ratio(phiy_mm, py_mm, phiaddy_mm, paddy_mm, d_mm)
    return (rho_x * rho_y) ** 0.5
