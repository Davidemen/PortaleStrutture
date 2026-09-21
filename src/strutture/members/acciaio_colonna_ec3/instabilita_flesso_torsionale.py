"""Lateral-torsional buckling (column-check!AI8, S34/AI35, W36, U37, O59 — EN1993-1-1 §6.3.2.2/6.3.2.3).

New divergence (found by direct cell-formula inspection): `U37` (chi_LT) computes
`1/(phi_LT + sqrt(lambda_LT^2 - beta*lambda_LT^2))` — the radicand is `lambda_LT^2*(1-beta)`, not
the standard EC3 §6.3.2.2 `phi_LT^2 - beta*lambda_LT^2` (the `phi_LT^2` term is missing). Fixed
behaviour uses the standard formula; legacy reproduces the sheet's. See
docs/divergences/acciaio-colonna-ec3.md.

Fixed divergence: `S34`/`AI35` (lambda_LT) use fyd = fyk/gammaM0, but EN1993-1-1 §6.3.2.2 eq.
(6.56) is `lambda_bar_LT = sqrt(Wy*fy/Mcr)` on the CHARACTERISTIC fy. Fixed mode uses fyk; legacy
reproduces fyd (invisible while gammaM0=1).
"""
import math

from .results import InstabilitaTorsoFlessionale
from .tables import BETA_LT, LAMBDA_LT_0


def momento_critico_Nmm(
    c1: float, e_MPa: float, izz_mm4: float, lt_mm: float, iw_mm6: float, g_MPa: float, it_mm4: float
) -> float:
    """column-check!AI8 — 3-factor (C1) Mcr, EC3-ENV Annex F / ECCS formula, using lT (not Lcr,zz)."""
    termine_base = math.pi**2 * e_MPa * izz_mm4 / lt_mm**2
    radice = (iw_mm6 / izz_mm4) + (lt_mm**2 * g_MPa * it_mm4) / (math.pi**2 * e_MPa * izz_mm4)
    return c1 * termine_base * math.sqrt(radice)


def snellezza_lt(classe_num: int, wel_y_mm3: float, wpl_y_mm3: float, fy_MPa: float, mcr_Nmm: float) -> float:
    """column-check!S34/AI35 — lambda_LT = sqrt(W*fy/Mcr); W=Wpl,y for class 1/2, Wel,y for 3/4;
    fy = fyk (fixed) or fyd (legacy)."""
    modulo = wpl_y_mm3 if classe_num < 3 else wel_y_mm3
    return math.sqrt(modulo * fy_MPa / mcr_Nmm)


def fattore_phi_lt(alpha_lt: float, lambda_lt: float) -> float:
    """column-check!W36 — phi_LT = 0.5*(1+alpha_LT*(lambda_LT-lambda_LT,0)+beta*lambda_LT^2)."""
    return 0.5 * (1.0 + alpha_lt * (lambda_lt - LAMBDA_LT_0) + BETA_LT * lambda_lt**2)


def fattore_chi_lt(phi_lt: float, lambda_lt: float, *, legacy_compat: bool) -> float:
    """column-check!U37 — chi_LT, capped at MIN(..., 1, 1/lambda_LT^2); see module docstring."""
    radicando = lambda_lt**2 * (1.0 - BETA_LT) if legacy_compat else phi_lt**2 - BETA_LT * lambda_lt**2
    return min(1.0 / (phi_lt + math.sqrt(radicando)), 1.0, 1.0 / lambda_lt**2)


def ltb_non_necessaria(my_sd_kNm: float, mz_sd_kNm: float, mcr_Nmm: float, lambda_lt: float) -> bool:
    """column-check!O59 — EN1993-1-1 §6.3.2.2(4) exemption."""
    return (max(my_sd_kNm, mz_sd_kNm) * 1_000_000.0 / mcr_Nmm) < LAMBDA_LT_0**2 or lambda_lt < LAMBDA_LT_0


def costruisci_ltb(
    *,
    c1: float,
    e_MPa: float,
    izz_mm4: float,
    lt_mm: float,
    iw_mm6: float,
    g_MPa: float,
    it_mm4: float,
    classe_num: int,
    wel_y_mm3: float,
    wpl_y_mm3: float,
    fyd_MPa: float,
    fyk_MPa: float,
    alpha_lt: float,
    my_sd_kNm: float,
    mz_sd_kNm: float,
    legacy_compat: bool,
) -> InstabilitaTorsoFlessionale:
    mcr = momento_critico_Nmm(c1, e_MPa, izz_mm4, lt_mm, iw_mm6, g_MPa, it_mm4)
    fy_lambda = fyd_MPa if legacy_compat else fyk_MPa
    lambda_lt = snellezza_lt(classe_num, wel_y_mm3, wpl_y_mm3, fy_lambda, mcr)
    phi_lt = fattore_phi_lt(alpha_lt, lambda_lt)
    return InstabilitaTorsoFlessionale(
        mcr_Nmm=mcr,
        lambda_lt=lambda_lt,
        phi_lt=phi_lt,
        chi_lt=fattore_chi_lt(phi_lt, lambda_lt, legacy_compat=legacy_compat),
        verifica_non_necessaria=ltb_non_necessaria(my_sd_kNm, mz_sd_kNm, mcr, lambda_lt),
    )
