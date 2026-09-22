"""N-My-Mz interaction, EN1993-1-1 §6.3.3 eq. 6.61/6.62, Annex A kij (column-check!Y47, Y50).

New divergence (found by direct cell-formula inspection): `Y47`'s (eq. 6.61, yy) third term is
`X43*J21/Q40/H13` — missing the parentheses around `Q40/H13` that its own first two terms use (and
that `Y50`'s (eq. 6.62, zz) third term `X45*J21/(Q40/H13)` does have — so `Y50` is the consistent
one. `Y47`'s term therefore evaluates to `kyz*Mz,sd/(Mpl,z*gammaM1)` instead of
`kyz*Mz,sd/(Mpl,z/gammaM1)` — an extra `gammaM1` division invisible while gammaM1=1 (the sheet's
own bugged default, see `materiale.py`). Fixed behaviour mirrors `Y50`'s grouping for both
equations; legacy reproduces `Y47`'s asymmetry. See docs/divergences/acciaio-colonna-ec3.md.

Fixed divergence: `Q41`/`Q39`/`Q40` (npl_kN, mpl_y_kNm, mpl_z_kNm) are built from fyd = fyk/gammaM0,
and `Y47`/`Y50` then divide by gammaM1 again — so every term of eq. 6.61/6.62 is effectively
divided by gammaM0*gammaM1. EN1993-1-1 §6.3.3 eq. (6.61)/(6.62) require the CHARACTERISTIC
resistances NRk=A*fyk, Mi,Rk=Wi*fyk divided by gammaM1 ONLY. Fixed mode uses the characteristic
resistances (`sezione.npl_rk_kN`/`mpl_y_rk_kNm`/`mpl_z_rk_kNm`); legacy reproduces the
design-strength-based ones (double gamma division included).
"""
from strutture.shared.divergences import legacy
from strutture.shared.report import Check

from . import annex_a_cm as cm
from . import annex_a_kij as kij
from .models import ColonnaEc3Input
from .results import Interazione


def _utilizzo(nsd_kN: float, chi: float, npl_kN: float, gamma_m1: float, k_diretto: float, my_sd_kNm: float,
              chi_lt: float, mpl_y_kNm: float, k_incrociato: float, mz_sd_kNm: float, mpl_z_kNm: float,
              *, gamma_extra_terzo_termine: bool) -> float:
    """column-check!Y47/Y50 — N/(chi*Npl/gM1) + k*My/(chiLT*Mpl,y/gM1) + k*Mz/(Mpl,z/gM1)."""
    termine_n = nsd_kN / (chi * npl_kN / gamma_m1)
    termine_my = k_diretto * my_sd_kNm / (chi_lt * mpl_y_kNm / gamma_m1)
    denominatore_mz = (
        mpl_z_kNm * gamma_m1
        if legacy("acciaio-colonna-ec3/eq-6-61-terzo-termine-gamma-m1-extra", gamma_extra_terzo_termine)
        else mpl_z_kNm / gamma_m1
    )
    termine_mz = k_incrociato * mz_sd_kNm / denominatore_mz
    return termine_n + termine_my + termine_mz


def _fattori_c_e_k(
    *, inputs: ColonnaEc3Input, classe_num: int, area_mm2: float, mpl_y_kNm: float, mpl_z_kNm: float,
    wy: float, wz: float, wel_y_mm3: float, wpl_y_mm3: float, wel_z_mm3: float, wpl_z_mm3: float,
    ncr_y_kN: float, ncr_z_kN: float, ncr_t_kN: float, chi_yy: float, chi_zz: float, chi_lt: float,
    lambda_max: float, lambda_zz: float, lambda_lt: float, alpha_lt_torsione: float, n_pl: float,
) -> tuple[float, float, float, float, float, float, float]:
    """Cmy/Cmz/CmLT (Annex A Tab. A.2) e kyy/kyz/kzy/kzz (Annex A Tab. A.1)."""
    nsd, my_sd, mz_sd = inputs.nsd_kN, inputs.my_sd_kNm, inputs.mz_sd_kNm
    n_y, n_z = nsd / ncr_y_kN, nsd / ncr_z_kN
    eps_y = cm.epsilon_y(my_sd, area_mm2, nsd, wel_y_mm3)
    soglia = cm.soglia_lambda0(inputs.c1, nsd, ncr_z_kN, ncr_t_kN)
    cmy_val = cm.cmy(
        inputs.diagramma_tipo_y, lambda_lt, soglia, my_sd, inputs.mj_y_kNm, inputs.e_MPa, inputs.iyy_mm4,
        inputs.dmax_yy_mm, inputs.lcr_yy_mm, nsd, ncr_y_kN, alpha_lt_torsione, eps_y,
    )
    cmz_val = cm.cmz(
        inputs.diagramma_tipo_z, mz_sd, inputs.mj_z_kNm, inputs.e_MPa, inputs.iyy_mm4, inputs.izz_mm4,
        inputs.dmax_zz_mm, inputs.lcr_zz_mm, nsd, ncr_z_kN, legacy_compat=inputs.legacy_compat,
    )
    cm_lt_val = cm.cm_lt(lambda_lt, soglia, cmy_val, alpha_lt_torsione, nsd, ncr_z_kN, ncr_t_kN)
    mu_y = kij.fattore_mu(nsd, ncr_y_kN, chi_yy)
    mu_z = kij.fattore_mu(nsd, ncr_z_kN, chi_zz)
    cyy_val = kij.cyy(wy, cmy_val, lambda_max, n_pl, alpha_lt_torsione, lambda_lt, chi_lt, my_sd, mz_sd, mpl_y_kNm, mpl_z_kNm, wel_y_mm3, wpl_y_mm3)
    cyz_val = kij.cyz(wy, wz, cmy_val, cmz_val, chi_lt, lambda_max, lambda_lt, lambda_zz, n_pl, alpha_lt_torsione, my_sd, mpl_y_kNm, wel_z_mm3, wpl_z_mm3)
    czy_val = kij.czy(
        wy, wz, cmy_val, cmz_val, chi_lt, lambda_max, lambda_lt, lambda_zz, n_pl, alpha_lt_torsione, my_sd, mz_sd,
        mpl_y_kNm, mpl_z_kNm, wel_y_mm3, wpl_y_mm3, legacy_compat=inputs.legacy_compat,
    )
    czz_val = kij.czz(wz, cmy_val, cmz_val, chi_lt, lambda_max, lambda_lt, lambda_zz, n_pl, alpha_lt_torsione, my_sd, mpl_y_kNm, wel_z_mm3, wpl_z_mm3)
    kyy_val = kij.kyy(classe_num, cmy_val, cm_lt_val, mu_y, n_y, cyy_val)
    kyz_val = kij.kyz(classe_num, cmz_val, mu_y, n_z, cyz_val, wy, wz)
    kzy_val = kij.kzy(classe_num, cmy_val, cm_lt_val, mu_z, n_y, czy_val, wy, wz)
    kzz_val = kij.kzz(classe_num, cmz_val, mu_z, n_z, czz_val)
    return cmy_val, cmz_val, cm_lt_val, kyy_val, kyz_val, kzy_val, kzz_val


def _denominatori_resistenza(
    *, legacy_compat: bool, npl_kN: float, mpl_y_kNm: float, mpl_z_kNm: float,
    npl_rk_kN: float, mpl_y_rk_kNm: float, mpl_z_rk_kNm: float,
) -> tuple[float, float, float]:
    """EN1993-1-1 §6.3.3 eq. 6.61/6.62: resistenze caratteristiche (NRk, Mi,Rk) in modalità standard;
    la modalità Excel riproduce Npl/Mpl del foglio (già con gammaM0 incorporato)."""
    doppia_divisione = legacy("acciaio-colonna-ec3/interazione-doppia-divisione-gamma-m0-m1", legacy_compat)
    npl_denom = npl_kN if doppia_divisione else npl_rk_kN
    mpl_y_denom = mpl_y_kNm if doppia_divisione else mpl_y_rk_kNm
    mpl_z_denom = mpl_z_kNm if doppia_divisione else mpl_z_rk_kNm
    return npl_denom, mpl_y_denom, mpl_z_denom


def _verifica_utilizzo(asse: str, clausola: str, utilizzo: float) -> Check:
    """column-check!Y47/Y50 < 1 — nome ed etichetta comuni alle verifiche yy/zz."""
    return Check(
        name=f"Interazione N-My-Mz ({asse})", passed=utilizzo < 1.0, detail=f"utilizzo={utilizzo:.4f} < 1",
        clause=clausola, value=utilizzo, limit=1.0, unit="-",
    )


def costruisci_interazione(
    *, inputs: ColonnaEc3Input, classe_num: int, gamma_m1: float, area_mm2: float,
    npl_kN: float, mpl_y_kNm: float, mpl_z_kNm: float,
    npl_rk_kN: float, mpl_y_rk_kNm: float, mpl_z_rk_kNm: float,
    wy: float, wz: float,
    wel_y_mm3: float, wpl_y_mm3: float, wel_z_mm3: float, wpl_z_mm3: float,
    ncr_y_kN: float, ncr_z_kN: float, ncr_t_kN: float, chi_yy: float, chi_zz: float, chi_lt: float,
    lambda_max: float, lambda_zz: float, lambda_lt: float, alpha_lt_torsione: float,
) -> Interazione:
    nsd, my_sd, mz_sd = inputs.nsd_kN, inputs.my_sd_kNm, inputs.mz_sd_kNm
    n_pl = nsd / npl_kN
    cmy_val, cmz_val, cm_lt_val, kyy_val, kyz_val, kzy_val, kzz_val = _fattori_c_e_k(
        inputs=inputs, classe_num=classe_num, area_mm2=area_mm2, mpl_y_kNm=mpl_y_kNm, mpl_z_kNm=mpl_z_kNm,
        wy=wy, wz=wz, wel_y_mm3=wel_y_mm3, wpl_y_mm3=wpl_y_mm3, wel_z_mm3=wel_z_mm3, wpl_z_mm3=wpl_z_mm3,
        ncr_y_kN=ncr_y_kN, ncr_z_kN=ncr_z_kN, ncr_t_kN=ncr_t_kN, chi_yy=chi_yy, chi_zz=chi_zz, chi_lt=chi_lt,
        lambda_max=lambda_max, lambda_zz=lambda_zz, lambda_lt=lambda_lt, alpha_lt_torsione=alpha_lt_torsione,
        n_pl=n_pl,
    )
    npl_denom, mpl_y_denom, mpl_z_denom = _denominatori_resistenza(
        legacy_compat=inputs.legacy_compat, npl_kN=npl_kN, mpl_y_kNm=mpl_y_kNm, mpl_z_kNm=mpl_z_kNm,
        npl_rk_kN=npl_rk_kN, mpl_y_rk_kNm=mpl_y_rk_kNm, mpl_z_rk_kNm=mpl_z_rk_kNm,
    )
    utilizzo_yy = _utilizzo(
        nsd, chi_yy, npl_denom, gamma_m1, kyy_val, my_sd, chi_lt, mpl_y_denom, kyz_val, mz_sd, mpl_z_denom,
        gamma_extra_terzo_termine=inputs.legacy_compat,
    )
    utilizzo_zz = _utilizzo(
        nsd, chi_zz, npl_denom, gamma_m1, kzy_val, my_sd, chi_lt, mpl_y_denom, kzz_val, mz_sd, mpl_z_denom,
        gamma_extra_terzo_termine=False,
    )
    return Interazione(
        cmy=cmy_val, cmz=cmz_val, cm_lt=cm_lt_val,
        kyy=kyy_val, kyz=kyz_val, kzy=kzy_val, kzz=kzz_val,
        utilizzo_yy=utilizzo_yy, utilizzo_zz=utilizzo_zz,
        verifica_yy=_verifica_utilizzo("yy", "EN1993-1-1 §6.3.3 eq. 6.61", utilizzo_yy),
        verifica_zz=_verifica_utilizzo("zz", "EN1993-1-1 §6.3.3 eq. 6.62", utilizzo_zz),
    )
