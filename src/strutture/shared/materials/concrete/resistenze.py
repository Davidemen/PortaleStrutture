"""NTC2018 §4.1.2.1.1 — concrete strength/stiffness derived from fck (Circolare 7/2019 Tab. C4.1.I)."""
CEMENT_AGING_EXPONENT = 0.3  # NTC2018 §4.1.2.1.1 — esponente della legge Ecm = 22000*(fcm/10)^0.3
FCM_OVER_FCK_MPA = 8.0  # NTC2018 §4.1.2.1.1 — fcm = fck + 8 MPa
FCTM_COEFFICIENT = 0.30  # NTC2018 §4.1.2.1.1 — fctm = 0.30*fck^(2/3), valido per classi <= C50/60
FCTM_EXPONENT = 2.0 / 3.0
FCTK_OVER_FCTM = 0.7  # NTC2018 §4.1.2.1.1 — fctk (frattile 5%) = 0.7*fctm


def fcm(fck_MPa: float) -> float:
    """fcm = fck + 8, MPa."""
    return fck_MPa + FCM_OVER_FCK_MPA


def ecm(fcm_MPa: float) -> float:
    """Ecm = 22000*(fcm/10)^0.3, MPa."""
    return 22000.0 * (fcm_MPa / 10.0) ** CEMENT_AGING_EXPONENT


def fctm(fck_MPa: float) -> float:
    """fctm = 0.30*fck^(2/3), MPa (classi di resistenza <= C50/60)."""
    return FCTM_COEFFICIENT * fck_MPa**FCTM_EXPONENT


def fctk(fctm_MPa: float) -> float:
    """fctk = 0.7*fctm, MPa (frattile 5%)."""
    return FCTK_OVER_FCTM * fctm_MPa
