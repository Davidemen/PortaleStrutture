"""Flexural buckling reduction factors (column-check!W23, W24, W27-W29, W32 — EN1993-1-1 §6.3.1.2/3).

Fixed divergence (docs/divergences/acciaio-colonna-ec3.md): the sheet's `W23`/`W24` compute
`lambda_bar = sqrt(A*fyd/Ncr)` with fyd = fyk/gammaM0, but EN1993-1-1 §6.3.1.2 eq. (6.50) is
`lambda_bar = sqrt(A*fy/Ncr)` on the CHARACTERISTIC fy (NRk = A*fy) — gammaM0 must not appear.
Invisible while gammaM0=1 (the sheet's own bugged default, item 1); fixed mode uses fyk, legacy
reproduces fyd.
"""
import math

from strutture.shared.units import kn_to_n

from .results import InstabilitaFlessionale


def snellezza_adimensionale(area_mm2: float, fy_MPa: float, ncr_kN: float) -> float:
    """column-check!W23/W24 — lambda_bar = sqrt(A*fy/Ncr); fy = fyk (fixed) or fyd (legacy)."""
    return math.sqrt(area_mm2 * fy_MPa / kn_to_n(ncr_kN))


def fattore_phi(alpha: float, lambda_bar: float) -> float:
    """column-check!W27/W28 — phi = 0.5*(1+alpha*(lambda_bar-0.2)+lambda_bar^2)."""
    return 0.5 * (1.0 + alpha * (lambda_bar - 0.2) + lambda_bar**2)


def fattore_chi(phi: float, lambda_bar: float) -> float:
    """column-check!W29/W32 — chi = MIN(1, 1/(phi+sqrt(phi^2-lambda_bar^2)))."""
    return min(1.0, 1.0 / (phi + math.sqrt(phi**2 - lambda_bar**2)))


def costruisci_instabilita_flessionale(
    *,
    area_mm2: float,
    fyd_MPa: float,
    fyk_MPa: float,
    ncr_y_kN: float,
    ncr_z_kN: float,
    ncr_t_kN: float,
    alpha_yy: float,
    alpha_zz: float,
    legacy_compat: bool,
) -> InstabilitaFlessionale:
    fy_lambda = fyd_MPa if legacy_compat else fyk_MPa
    lambda_yy = snellezza_adimensionale(area_mm2, fy_lambda, ncr_y_kN)
    lambda_zz = snellezza_adimensionale(area_mm2, fy_lambda, ncr_z_kN)
    phi_yy = fattore_phi(alpha_yy, lambda_yy)
    phi_zz = fattore_phi(alpha_zz, lambda_zz)
    return InstabilitaFlessionale(
        ncr_y_kN=ncr_y_kN,
        ncr_z_kN=ncr_z_kN,
        ncr_t_kN=ncr_t_kN,
        lambda_yy=lambda_yy,
        lambda_zz=lambda_zz,
        lambda_max=max(lambda_yy, lambda_zz),
        phi_yy=phi_yy,
        phi_zz=phi_zz,
        chi_yy=fattore_chi(phi_yy, lambda_yy),
        chi_zz=fattore_chi(phi_zz, lambda_zz),
    )
