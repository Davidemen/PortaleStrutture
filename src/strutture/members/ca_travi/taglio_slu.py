"""Tool 3 — verifica-taglio-slu: traliccio a inclinazione variabile con 1 ≤ cotθ ≤ 2.5
(NTC2018 §4.1.2.3.5.2 / EC2 6.2.3).

Stessa formula in entrambe le modalità: il foglio non presenta un bug noto su questo step
(usa correttamente il braccio di leva z, coerente con la convenzione EC2 z≈0.9d per il taglio).
"""
import math

from strutture.shared.numeric import clamp
from strutture.shared.report import CalcError
from strutture.shared.units import mm2_per_m_to_mm2_per_mm, n_to_kn

from .models import TaglioOutput

RIDUZIONE_RESISTENZA_CLS = 0.5  # NTC2018 §4.1.2.3.5.2 — ν, riduzione della resistenza a compressione del puntone
COTG_THETA_MIN = 1.0  # NTC2018 §4.1.2.3.5.2
COTG_THETA_MAX = 2.5  # NTC2018 §4.1.2.3.5.2


def _cotangente(angolo_rad: float) -> float:
    return math.cos(angolo_rad) / math.sin(angolo_rad)


def cotangente_puntoni(asw_per_mm_mm2: float, fyd_MPa: float, b_mm: float, fcd_MPa: float) -> float:
    """cotθ (Z22), clampato in [1, 2.5]."""
    sin2_theta = asw_per_mm_mm2 * fyd_MPa / (b_mm * RIDUZIONE_RESISTENZA_CLS * fcd_MPa)
    if not 0.0 < sin2_theta <= 1.0:
        raise CalcError(f"armatura a taglio non valida: sin²θ={sin2_theta:.4g} fuori dall'intervallo (0,1]")
    cotg_theta_raw = math.sqrt((1.0 - sin2_theta) / sin2_theta)
    return clamp(cotg_theta_raw, COTG_THETA_MIN, COTG_THETA_MAX)


def verifica_taglio_slu(
    *, b_mm: float, z_mm: float, asw_per_m_mm2: float, fyd_MPa: float, fcd_MPa: float, alpha_staffe_deg: float
) -> TaglioOutput:
    alpha_rad = math.radians(alpha_staffe_deg)
    cotg_alpha = _cotangente(alpha_rad)
    asw_per_mm_mm2 = mm2_per_m_to_mm2_per_mm(asw_per_m_mm2)
    cotg_theta = cotangente_puntoni(asw_per_mm_mm2, fyd_MPa, b_mm, fcd_MPa)

    vrdc_kN = n_to_kn(z_mm * b_mm * RIDUZIONE_RESISTENZA_CLS * fcd_MPa * (cotg_alpha + cotg_theta) / (1.0 + cotg_theta**2))
    vrds_kN = n_to_kn(z_mm * asw_per_mm_mm2 * fyd_MPa * (cotg_alpha + cotg_theta) * math.sin(alpha_rad))

    return TaglioOutput(cotg_theta=cotg_theta, vrdc_kN=vrdc_kN, vrds_kN=vrds_kN, vrd_kN=min(vrdc_kN, vrds_kN))
