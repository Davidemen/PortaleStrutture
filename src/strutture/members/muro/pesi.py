"""Per-combination self-weight of wall and backfill (muro-sostegno rows 45-50/80-81, cols D-I/N-S)."""
from typing import NamedTuple

from .models import GeometriaResult


class PesiCombo(NamedTuple):
    w_muro_kN: float
    m_muro_kNm: float
    w_terr_kN: float
    m_terr_kNm: float


def pesi_combo(
    *,
    gamma_cls_kN_m3: float,
    gamma_terr_sat_kN_m3: float,
    geometria: GeometriaResult,
    gamma_g_muro: float,
    gamma_g_terr: float,
    kv_factor: float = 1.0,
) -> PesiCombo:
    """`kv_factor` = (1±kv) — EN1998-5 §7.3.2.2(2)P/NTC2018 §7.11.6.2.1 vertical seismic scaling of
    the monolith's own weight (1.0 for static combinations and for `legacy_compat=True`)."""
    w_muro_kN = gamma_cls_kN_m3 * geometria.a_muro_m2 * gamma_g_muro * kv_factor
    w_terr_kN = gamma_terr_sat_kN_m3 * geometria.a_terr_m2 * gamma_g_terr * kv_factor
    return PesiCombo(
        w_muro_kN=w_muro_kN,
        m_muro_kNm=w_muro_kN * geometria.x_muro_m,
        w_terr_kN=w_terr_kN,
        m_terr_kNm=w_terr_kN * geometria.x_terr_m,
    )
