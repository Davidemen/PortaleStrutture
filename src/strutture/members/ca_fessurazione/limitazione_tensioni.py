"""Step formulas for `ca-sle-limitazione-tensioni` (NTC2018 §4.1.2.2.5), sheet `Limitazione
delle tensioni`, calc steps 1-4."""

RAPPORTO_FCK_RCK = 0.83  # §11.2.10.1 — conversione Rck -> fck [C7]
COEFF_SIGMA_C_MAX_RAR = 0.6  # §4.1.2.2.5, combinazione rara, cls [C13/21/29]
COEFF_SIGMA_C_MAX_QPE = 0.45  # §4.1.2.2.5, combinazione quasi-permanente, cls [C14/22/30]
COEFF_SIGMA_S_MAX_RAR = 0.8  # §4.1.2.2.5, combinazione rara, armatura [C15/23/31]


def fck_da_rck(rck_MPa: float) -> float:
    """fck = 0.83*Rck [C7]."""
    return RAPPORTO_FCK_RCK * rck_MPa


def sigma_c_max_rar_MPa(fck_MPa: float) -> float:
    """σc,max,RAR = 0.6*fck [C13/21/29]."""
    return COEFF_SIGMA_C_MAX_RAR * fck_MPa


def sigma_c_max_qpe_MPa(fck_MPa: float) -> float:
    """σc,max,QPE = 0.45*fck [C14/22/30]."""
    return COEFF_SIGMA_C_MAX_QPE * fck_MPa


def sigma_s_max_rar_MPa(fyk_MPa: float) -> float:
    """σs,max,RAR = 0.8*fyk [C15/23/31]."""
    return COEFF_SIGMA_S_MAX_RAR * fyk_MPa
