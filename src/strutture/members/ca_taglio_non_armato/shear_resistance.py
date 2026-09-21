"""VRd,1 / VRd,2 / VRd (sheet B19:B21)."""
from strutture.shared.units import n_to_kn

from .tables import GAMMA_C, VRD1_COEFF, VRD1_SIGMA_CP_COEFF, VRD2_SIGMA_CP_COEFF


def vrd1_kN(k: float, rho_l: float, fck_MPa: float, sigma_cp_MPa: float, bw_mm: float, d_mm: float, *, gamma_c: float = GAMMA_C) -> float:
    """VRd,1 = [0.18*k*(100*rho_l*fck)^(1/3)/gamma_c + 0.15*sigma_cp]*bw*d, converted N->kN."""
    term_MPa = VRD1_COEFF * k * (100 * rho_l * fck_MPa) ** (1 / 3) / gamma_c + VRD1_SIGMA_CP_COEFF * sigma_cp_MPa
    return n_to_kn(term_MPa * bw_mm * d_mm)


def vrd2_kN(vmin_MPa: float, sigma_cp_MPa: float, bw_mm: float, d_mm: float) -> float:
    """VRd,2 = (vmin + 0.15*sigma_cp)*bw*d, converted N->kN."""
    term_MPa = vmin_MPa + VRD2_SIGMA_CP_COEFF * sigma_cp_MPa
    return n_to_kn(term_MPa * bw_mm * d_mm)


def vrd_kN(vrd1_kN: float, vrd2_kN: float) -> float:
    """VRd = MAX(VRd,1, VRd,2), kN."""
    return max(vrd1_kN, vrd2_kN)
