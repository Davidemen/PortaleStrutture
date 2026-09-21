"""Step formulas for `ca-apertura-fessure` section geometry (Circ. 2019 §C4.1.2.2.4.5, calc
steps 1-3), sheet `Apertura delle fessure`."""


def altezza_utile_mm(h_mm: float, phi1_mm: float, copriferro_mm: float) -> float:
    """d = h - ø1/2 - c [E24]."""
    return h_mm - phi1_mm / 2 - copriferro_mm


def altezza_efficace_mm(h_mm: float, d_mm: float, x_mm: float) -> float:
    """hc,ef = MIN(2.5*(h-d), (h-x)/3, h/2) [E22]."""
    return min(2.5 * (h_mm - d_mm), (h_mm - x_mm) / 3, h_mm / 2)


def area_efficace_mm2(hc_eff_mm: float, b_mm: float) -> float:
    """Ac,eff = hc,ef * b [E27]."""
    return hc_eff_mm * b_mm


def diametro_equivalente_mm(n1: int, phi1_mm: float, n2: int, phi2_mm: float) -> float:
    """øeq = (n1*ø1^2 + n2*ø2^2) / (n1*ø1 + n2*ø2) [E33], NTC §C4.1.8."""
    denominatore = n1 * phi1_mm + n2 * phi2_mm
    if denominatore <= 0:
        raise ValueError("almeno un gruppo di barre deve avere n>0 e ø>0")
    return (n1 * phi1_mm**2 + n2 * phi2_mm**2) / denominatore


def rapporto_armatura_efficace(as_mm2: float, ac_eff_mm2: float) -> float:
    """ρreff = As / Ac,eff [E36]."""
    if ac_eff_mm2 <= 0:
        raise ValueError("l'area efficace di calcestruzzo teso deve essere positiva")
    return as_mm2 / ac_eff_mm2
