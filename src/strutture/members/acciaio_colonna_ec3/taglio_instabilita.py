"""Web shear buckling (column-check!AC27, AD27, C67, G69, C76, I71, H74, O75 — EN1993-1-5 §5).

Only the "shear-buckling cap" branch of EN1993-1-5 Table 5.1 is implemented (`cw = 0.83/lambda_w`,
valid for `0.83/eta < lambda_w < 1.08`); the sheet never branches to the other two Table 5.1 rows —
Da verificare (docs/divergences/acciaio-colonna-ec3.md).

Fixed divergences (docs/divergences/acciaio-colonna-ec3.md):
- `epsilon`/`eta` (L30/L31) are keyed on the DESIGN strength fyd in the sheet; EN1993-1-1 Tab. 5.2
  and EN1993-1-5 §5.1 define both on the nominal/characteristic yield strength fyk. Fixed mode uses
  fyk; legacy reproduces fyd.
- `limite_hw_t` (AD27) multiplies by eta where EN1993-1-5 §5.1(2) divides, and `richiede_verifica`
  (K32) compares `hw/t <= limite` where the clause requires `hw/t > limite` (the check is required
  ABOVE the threshold, not below). Fixed mode implements `72*eps/eta` and `hw_t > limite`; legacy
  reproduces the sheet's `72*eps*eta` and `hw_t <= limite`.
"""
import math

from strutture.shared.numeric import clamp
from strutture.shared.report import Check
from strutture.shared.units import kn_to_n, n_to_kn, nmm_to_knm

from .results import TaglioInstabilita
from .tables import FATTORE_LIMITE_HW_T


def hw_su_t(h_mm: float, tf_mm: float, tw_mm: float) -> float:
    """column-check!AC27 — hw/tw."""
    return (h_mm - 2.0 * tf_mm) / tw_mm


def epsilon(fy_MPa: float) -> float:
    """column-check!L30 — epsilon = sqrt(235/fy); fy is fyk in fixed mode, fyd in legacy mode."""
    return math.sqrt(235.0 / fy_MPa)


def eta(fy_MPa: float) -> float:
    """column-check!L31 — eta = IF(fy>460,1,1.2); fy is fyk in fixed mode, fyd in legacy mode."""
    return 1.0 if fy_MPa > 460.0 else 1.2


def limite_hw_t(eps: float, et: float, *, legacy_compat: bool) -> float:
    """column-check!AD27 — 72*epsilon*eta (legacy) vs 72*epsilon/eta (EN1993-1-5 §5.1(2), fixed)."""
    return FATTORE_LIMITE_HW_T * eps * et if legacy_compat else FATTORE_LIMITE_HW_T * eps / et


def richiede_verifica_taglio(hw_t: float, limite: float, *, legacy_compat: bool) -> bool:
    """column-check!K32 — legacy reproduces `hw_t <= limite`; fixed uses EN1993-1-5 §5.1(2) `hw_t > limite`."""
    return hw_t <= limite if legacy_compat else hw_t > limite


def lambda_w(hw_mm: float, tw_mm: float, eps: float) -> float:
    """column-check!F65 — lambda_w = hw/(86.4*tw*epsilon)."""
    return hw_mm / (86.4 * tw_mm * eps)


def cw(lambda_w: float) -> float:
    """column-check!C67 — cw = 0.83/lambda_w."""
    return 0.83 / lambda_w


def vbw_rd_kN(cw: float, fyd_MPa: float, hw_mm: float, tw_mm: float, gamma_m1: float) -> float:
    """column-check!G69 — web contribution, EN1993-1-5 eq. 5.2."""
    return n_to_kn((cw * fyd_MPa * hw_mm * tw_mm) / (math.sqrt(3.0) * gamma_m1))


def vbw_rd_max_kN(eta: float, fyd_MPa: float, hw_mm: float, tw_mm: float, gamma_m1: float) -> float:
    """column-check!C76 — Vb,Rd cap = eta*fyd*hw*tw/(sqrt(3)*gammaM1)."""
    return n_to_kn((eta * fyd_MPa * hw_mm * tw_mm) / (math.sqrt(3.0) * gamma_m1))


def larghezza_efficace_ala_mm(b_mm: float, eps: float, tf_mm: float) -> float:
    """column-check!P66 — B = MIN(b, 15*epsilon*tf), EN1993-1-5 Annex A."""
    return min(b_mm, 15.0 * eps * tf_mm)


def fattore_c67_flangia(ly_mm: float, larghezza_efficace_mm: float, tf_mm: float, tw_mm: float, hw_mm: float) -> float:
    """column-check!V67 — c = a*(0.25+1.6*B*tf^2/(tw*hw^2)), EN1993-1-5 Annex A."""
    return ly_mm * (0.25 + (1.6 * larghezza_efficace_mm * tf_mm**2) / (tw_mm * hw_mm**2))


def momento_resistente_ali_kNm(b_mm: float, tf_mm: float, h_mm: float, fyd_MPa: float) -> float:
    """column-check!Q61 — Mf,k, plastic moment of resistance of the flanges only."""
    return nmm_to_knm(2.0 * (b_mm * tf_mm) * fyd_MPa * (h_mm / 2.0 - tf_mm / 2.0))


def fattore_riduzione_ali(nsd_kN: float, b_mm: float, tf_mm: float, fyd_MPa: float, gamma_m0: float) -> float:
    """column-check!Q62 — rf, reduction of the flange-only moment for axial force."""
    return clamp(1.0 - kn_to_n(nsd_kN) / (2.0 * b_mm * tf_mm * fyd_MPa / gamma_m0), 0.0, 1.0)


def vbf_rd_kN(b_mm: float, tf_mm: float, fyd_MPa: float, c67_flangia: float, gamma_m1: float, my_sd_kNm: float, mf_rd_kNm: float) -> float:
    """column-check!I71 — flange contribution, EN1993-1-5 §5.4(1)."""
    return n_to_kn(((b_mm * tf_mm**2 * fyd_MPa) / (c67_flangia * gamma_m1)) * (1.0 - (my_sd_kNm / mf_rd_kNm) ** 2))


def costruisci_taglio_instabilita(
    *, b_mm: float, h_mm: float, tw_mm: float, tf_mm: float, ly_mm: float, fyd_MPa: float, fyk_MPa: float,
    gamma_m0: float, gamma_m1: float, nsd_kN: float, my_sd_kNm: float, vy_sd_kN: float, legacy_compat: bool,
) -> TaglioInstabilita:
    hw_mm = h_mm - 2.0 * tf_mm
    hw_t = hw_su_t(h_mm, tf_mm, tw_mm)
    fy_eps_eta = fyd_MPa if legacy_compat else fyk_MPa
    eps = epsilon(fy_eps_eta)
    et = eta(fy_eps_eta)
    limite = limite_hw_t(eps, et, legacy_compat=legacy_compat)
    coeff_cw = cw(lambda_w(hw_mm, tw_mm, eps))
    vbw = vbw_rd_kN(coeff_cw, fyd_MPa, hw_mm, tw_mm, gamma_m1)
    vbw_max = vbw_rd_max_kN(et, fyd_MPa, hw_mm, tw_mm, gamma_m1)
    larghezza_eff = larghezza_efficace_ala_mm(b_mm, eps, tf_mm)
    c_flangia = fattore_c67_flangia(ly_mm, larghezza_eff, tf_mm, tw_mm, hw_mm)
    mfk = momento_resistente_ali_kNm(b_mm, tf_mm, h_mm, fyd_MPa)
    rf = fattore_riduzione_ali(nsd_kN, b_mm, tf_mm, fyd_MPa, gamma_m0)
    mf_rd = rf * mfk / gamma_m0
    vbf = vbf_rd_kN(b_mm, tf_mm, fyd_MPa, c_flangia, gamma_m1, my_sd_kNm, mf_rd)
    vb_rd = min(vbf + vbw, vbw_max)
    return TaglioInstabilita(
        hw_t=hw_t,
        limite_72_eps_eta=limite,
        richiede_verifica=richiede_verifica_taglio(hw_t, limite, legacy_compat=legacy_compat),
        cw=coeff_cw,
        vb_rd_kN=vb_rd,
        verifica=Check(
            name="Vb,Rd (instabilità taglio)", passed=vb_rd > vy_sd_kN,
            detail=f"Vb,Rd={vb_rd:.3f} kN > Vy,sd={vy_sd_kN:.3f} kN",
            clause="EN1993-1-5 §5", value=vy_sd_kN, limit=vb_rd, unit="kN",
        ),
    )
