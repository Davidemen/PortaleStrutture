"""Interaction factors kyy, kyz, kzy, kzz (EN1993-1-1 Annex A, Table A.1;
column-check!AI30-AI83). Class 1/2 sections use the full Cyy/Cyz/Czy/Czz-corrected formulas;
class 3/4 use the simpler forms (no Cij correction). The `cLT`/`dLT`/`eLT` correction terms
(`AL70`/`AL72`/`AL74`) divide by `lambda_zz` (column-check!W24, the z-z flexural slenderness), not
`chi_zz` (W32) — reproduced as-is in both modes, no bug flagged for this part.

Fixed divergence (docs/divergences/acciaio-colonna-ec3.md): `czy`'s bracket divides by `wz**5`
(`AL72`), reusing the pairing from `cyz` (which correctly divides by `wz**5` alongside `Cmz`).
EN1993-1-1 Annex A Table A.1 pairs `Czy`'s `Cmy`/`lambda_max` term with `wy**5`, matching the
`(wy - 1)` prefactor the code already uses. Legacy reproduces the sheet's `wz**5`; fixed mode uses
`wy**5`.
"""
import math


def fattore_mu(nsd_kN: float, ncr_kN: float, chi: float) -> float:
    """column-check!AI30/AN30 — mu = (1-Nsd/Ncr)/(1-chi*Nsd/Ncr)."""
    return (1.0 - nsd_kN / ncr_kN) / (1.0 - chi * nsd_kN / ncr_kN)


def cyy(wy: float, cmy: float, lambda_max: float, n_pl: float, alpha_lt: float, lambda_lt: float, chi_lt: float,
        my_sd_kNm: float, mz_sd_kNm: float, mpl_y_kNm: float, mpl_z_kNm: float, wel_y_mm3: float, wpl_y_mm3: float) -> float:
    """column-check!AI68/AL68 — Cyy (class 1/2)."""
    b_lt = 0.5 * alpha_lt * lambda_lt**2 * my_sd_kNm * mz_sd_kNm / (chi_lt * mpl_y_kNm * mpl_z_kNm)
    parentesi = (2.0 - (1.6 / wy) * cmy**2 * lambda_max - (1.6 / wy) * cmy**2 * lambda_max**2) * n_pl - b_lt
    return max(1.0 + (wy - 1.0) * parentesi, wel_y_mm3 / wpl_y_mm3)


def cyz(wy: float, wz: float, cmy: float, cmz: float, chi_lt: float, lambda_max: float, lambda_lt: float, lambda_zz: float,
        n_pl: float, alpha_lt: float, my_sd_kNm: float, mpl_y_kNm: float,
        wel_z_mm3: float, wpl_z_mm3: float) -> float:
    """column-check!AI70/AL70 — Cyz (class 1/2). Note: AL70 divides by `lambda_zz` (W24), not chi_zz."""
    c_lt = 10.0 * alpha_lt * (lambda_lt**2 / (5.0 + lambda_zz**4)) * (my_sd_kNm / (cmy * chi_lt * mpl_y_kNm))
    parentesi = (2.0 - 14.0 * (cmz**2 * lambda_max**2) / wz**5) * n_pl - c_lt
    return max(1.0 + (wz - 1.0) * parentesi, 0.6 * math.sqrt(wz / wy) * wel_z_mm3 / wpl_z_mm3)


def czy(wy: float, wz: float, cmy: float, cmz: float, chi_lt: float, lambda_max: float, lambda_lt: float, lambda_zz: float,
        n_pl: float, alpha_lt: float, my_sd_kNm: float, mz_sd_kNm: float, mpl_y_kNm: float, mpl_z_kNm: float,
        wel_y_mm3: float, wpl_y_mm3: float, *, legacy_compat: bool) -> float:
    """column-check!AI72/AL72 — Czy (class 1/2). Note: AL72 divides by `lambda_zz` (W24), not chi_zz.
    Legacy reproduces AL72's `wz**5`; fixed mode uses Table A.1's `wy**5` (see module docstring)."""
    d_lt = 2.0 * alpha_lt * (lambda_lt / (0.1 + lambda_zz**4)) * ((my_sd_kNm * mz_sd_kNm) / (cmy * chi_lt * mpl_y_kNm * cmz * mpl_z_kNm))
    w_potenza_5 = wz**5 if legacy_compat else wy**5
    parentesi = (2.0 - 14.0 * (cmy**2 * lambda_max**2) / w_potenza_5) * n_pl - d_lt
    return max(1.0 + (wy - 1.0) * parentesi, 0.6 * math.sqrt(wy / wz) * wel_y_mm3 / wpl_y_mm3)


def czz(wz: float, cmy: float, cmz: float, chi_lt: float, lambda_max: float, lambda_lt: float, lambda_zz: float,
        n_pl: float, alpha_lt: float, my_sd_kNm: float, mpl_y_kNm: float, wel_z_mm3: float, wpl_z_mm3: float) -> float:
    """column-check!AI74/AL74 — Czz (class 1/2). Note: AL74 divides by `lambda_zz` (W24), not chi_zz."""
    e_lt = 1.7 * alpha_lt * (lambda_lt / (0.1 + lambda_zz**4)) * (my_sd_kNm / (cmy * chi_lt * mpl_y_kNm))
    parentesi = (2.0 - (1.6 / wz) * cmz**2 * lambda_max - (1.6 / wz) * cmz**2 * lambda_max**2) * n_pl - e_lt
    return max(1.0 + (wz - 1.0) * parentesi, wel_z_mm3 / wpl_z_mm3)


def kyy(classe_num: int, cmy: float, cm_lt: float, mu_y: float, n_y: float, cyy: float) -> float:
    """column-check!AI77."""
    base = cmy * (mu_y / (1.0 - n_y))
    return cm_lt * base / cyy if classe_num <= 2 else cm_lt * base


def kyz(classe_num: int, cmz: float, mu_y: float, n_z: float, cyz: float, wy: float, wz: float) -> float:
    """column-check!AI79."""
    base = cmz * (mu_y / (1.0 - n_z))
    if classe_num <= 2:
        return (base / cyz) * 0.6 * math.sqrt(wz / wy)
    return base


def kzy(classe_num: int, cmy: float, cm_lt: float, mu_z: float, n_y: float, czy: float, wy: float, wz: float) -> float:
    """column-check!AI81."""
    base = cm_lt * cmy * (mu_z / (1.0 - n_y))
    if classe_num <= 2:
        return (base / czy) * 0.6 * math.sqrt(wy / wz)
    return base


def kzz(classe_num: int, cmz: float, mu_z: float, n_z: float, czz: float) -> float:
    """column-check!AI83."""
    base = cmz * (mu_z / (1.0 - n_z))
    return base / czz if classe_num <= 2 else base
