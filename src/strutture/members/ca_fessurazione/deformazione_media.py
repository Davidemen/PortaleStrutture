"""Mean strain in the tension rebar for `ca-apertura-fessure` (Circ. 2019 §C4.1.6), calc step 12."""

COEFF_DEFORMAZIONE_MINIMA = 0.6  # §C4.1.6 — limite inferiore (minimo tension-stiffening)


def deformazione_media_armatura(
    sigma_s_MPa: float, kt: float, fctm_MPa: float, rho_eff: float, alpha_e: float, es_MPa: float
) -> float:
    """εsm = MAX((σs - kt*fctm/ρreff*(1+αe*ρreff))/Es, 0.6*σs/Es) [E45]."""
    if rho_eff <= 0:
        raise ValueError("rho_eff deve essere positivo")
    if es_MPa <= 0:
        raise ValueError("es_MPa deve essere positivo")
    ramo_tension_stiffening = (sigma_s_MPa - kt * fctm_MPa / rho_eff * (1 + alpha_e * rho_eff)) / es_MPa
    ramo_minimo = COEFF_DEFORMAZIONE_MINIMA * sigma_s_MPa / es_MPa
    return max(ramo_tension_stiffening, ramo_minimo)
