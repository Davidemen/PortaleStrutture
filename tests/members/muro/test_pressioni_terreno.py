"""Unit tests for Tool 3 physics (EC7 Annex D / NTC2018 §6.4.2.1, rows 66-72/92-95)."""
import pytest

from strutture.members.muro.pressioni_terreno import (
    eccentricita_risultante,
    eccentricita_termine,
    larghezza_efficace,
    pressioni_valle_monte,
)

pytestmark = pytest.mark.unit


def test_eccentricita_termine_tratto_a_muro():
    e_m, m_kNm = eccentricita_termine(47.385, 0.661523, 1.9)
    assert e_m == pytest.approx(0.288477, rel=1e-5)
    assert m_kNm == pytest.approx(13.6695, rel=1e-4)


def test_eccentricita_risultante_str1():
    m_tot, e = eccentricita_risultante(m_rib_kNm=30.7784, m_muro_ecc_kNm=13.6695, m_terr_ecc_kNm=-26.5063, m_sv_ecc_kNm=0.0, n_tot_kN=118.069)
    assert m_tot == pytest.approx(17.9416, rel=1e-4)
    assert e == pytest.approx(0.151959, rel=1e-4)


def test_larghezza_efficace_entro_nocciolo_is_zero():
    assert larghezza_efficace(eccentricita_m=0.151959, b_fond_m=1.9) == pytest.approx(0.0)


def test_larghezza_efficace_outside_kern_sisma1():
    assert larghezza_efficace(eccentricita_m=0.399909, b_fond_m=1.9) == pytest.approx(1.65027, rel=1e-4)


def test_pressioni_valle_monte_trapezio_str1():
    pressioni = pressioni_valle_monte(n_tot_kN=118.069, m_tot_kNm=17.9416, b_fond_m=1.9, b_star_m=0.0)
    assert pressioni.p_valle_kPa == pytest.approx(91.9612, rel=1e-4)
    assert pressioni.p_monte_kPa == pytest.approx(32.3216, rel=1e-4)


def test_pressioni_valle_monte_triangolo_sisma1():
    pressioni = pressioni_valle_monte(n_tot_kN=90.822, m_tot_kNm=36.3206, b_fond_m=1.9, b_star_m=1.65027)
    assert pressioni.p_valle_kPa == pytest.approx(110.069, rel=1e-4)
    assert pressioni.p_monte_kPa == pytest.approx(0.0)


def test_pressioni_valle_monte_negative_moment_uplift_branch():
    """M<0 with B*>0: the uplift is at the opposite edge (pmonte carries the resultant)."""
    pressioni = pressioni_valle_monte(n_tot_kN=50.0, m_tot_kNm=-10.0, b_fond_m=2.0, b_star_m=0.5)
    assert pressioni.p_valle_kPa == pytest.approx(0.0)
    assert pressioni.p_monte_kPa == pytest.approx(2 * 50.0 / 0.5)
