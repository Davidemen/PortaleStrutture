"""Unit tests for `pesi_combo` (muro-sostegno rows 45-50/80-81, cols D-I/N-S)."""
import pytest

from strutture.members.muro.geometria import geometria_muro
from strutture.members.muro.pesi import pesi_combo

pytestmark = pytest.mark.unit


def test_pesi_combo_tratto_a_str1():
    geometria = geometria_muro(h_muro_m=2.4, s_fond_m=0.3, s_base_m=0.49, s_top_m=0.25, b_valle_m=0.26, b_monte_m=1.15)
    pesi = pesi_combo(gamma_cls_kN_m3=25, gamma_terr_sat_kN_m3=19.7, geometria=geometria, gamma_g_muro=1.3, gamma_g_terr=1.3)
    assert pesi.w_muro_kN == pytest.approx(47.385)
    assert pesi.m_muro_kNm == pytest.approx(31.3462, rel=1e-5)
    assert pesi.w_terr_kN == pytest.approx(70.6836, rel=1e-5)
    assert pesi.m_terr_kNm == pytest.approx(93.6558, rel=1e-5)
