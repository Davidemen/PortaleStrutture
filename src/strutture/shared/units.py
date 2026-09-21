"""Unit conversions. Field names carry their unit (b_mm, ned_kN, fcd_MPa); convert only through these."""

N_PER_KN = 1000.0
MM_PER_M = 1000.0
NMM_PER_KNM = 1_000_000.0
KPA_PER_MPA = 1000.0  # 1 MPa = 1 N/mm² = 1000 kN/m²
KPA_PER_KGCM2 = 98.0665  # 1 kgf/cm² (geotechnical sheets) = 98.0665 kPa
CM_PER_M = 100.0
MM_PER_CM = 10.0
GRAVITY_M_S2 = 9.80665  # standard gravity, the value the geotechnical sheets use


def kn_to_n(force_kn: float) -> float:
    return force_kn * N_PER_KN


def n_to_kn(force_n: float) -> float:
    return force_n / N_PER_KN


def mm2_per_m_to_mm2_per_mm(area_mm2_per_m: float) -> float:
    """Area per unit length: mm²/m -> mm²/mm."""
    return area_mm2_per_m / MM_PER_M


def m_to_mm(length_m: float) -> float:
    return length_m * MM_PER_M


def mm_to_m(length_mm: float) -> float:
    return length_mm / MM_PER_M


def knm_to_nmm(moment_knm: float) -> float:
    return moment_knm * NMM_PER_KNM


def nmm_to_knm(moment_nmm: float) -> float:
    return moment_nmm / NMM_PER_KNM


def mpa_to_kpa(stress_mpa: float) -> float:
    return stress_mpa * KPA_PER_MPA


def kgcm2_to_kpa(stress_kgcm2: float) -> float:
    return stress_kgcm2 * KPA_PER_KGCM2


def kpa_to_kgcm2(stress_kpa: float) -> float:
    return stress_kpa / KPA_PER_KGCM2


def kgcm2_to_mpa(stress_kgcm2: float) -> float:
    return stress_kgcm2 * KPA_PER_KGCM2 / KPA_PER_MPA


def cm_to_m(length_cm: float) -> float:
    return length_cm / CM_PER_M


def m_to_cm(length_m: float) -> float:
    return length_m * CM_PER_M


def mm_to_cm(length_mm: float) -> float:
    return length_mm / MM_PER_CM


def cm_to_mm(length_cm: float) -> float:
    return length_cm * MM_PER_CM


def kgm3_to_knm3(density_kgm3: float) -> float:
    """Mass density [kg/m³] -> unit weight [kN/m³]."""
    return density_kgm3 * GRAVITY_M_S2 / N_PER_KN
