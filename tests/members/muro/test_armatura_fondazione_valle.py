"""Unit tests for `armatura_fondazione_valle` (muro-sostegno rows 154-169), Tratto A values."""
import pytest

from strutture.members.muro import armatura_fondazione_valle as fond_valle

pytestmark = pytest.mark.unit


def test_pressione_interpolata_trapezio_branch_str1():
    """B*=0 (STR_1, entro nocciolo) -> interpolazione tra pmonte e pvalle sul trapezio."""
    p_star = fond_valle.pressione_interpolata_kPa(b_star_m=0.0, p_valle_kPa=91.9612, p_monte_kPa=32.3216, b_fond_m=1.9, x_star_m=0.26)
    assert p_star == pytest.approx(83.79995787901117, rel=1e-6)


def test_pressione_interpolata_triangolo_branch_sisma1():
    """B*>0 (SISMA_1, fuori nocciolo) -> interpolazione lineare sul triangolo di pressione."""
    p_star = fond_valle.pressione_interpolata_kPa(b_star_m=1.6502723847813994, p_valle_kPa=110.06910233431626, p_monte_kPa=0.0, b_fond_m=1.9, x_star_m=0.26)
    assert p_star == pytest.approx(92.72774288915225, rel=1e-6)


def test_momento_pressione_1_kNm_uses_smaller_of_p_star_and_p_valle():
    assert fond_valle.momento_pressione_1_kNm(p_star_kPa=83.8, p_valle_kPa=91.96, b_valle_m=0.26) == pytest.approx(83.8 * 0.26**2 / 2)
    assert fond_valle.momento_pressione_1_kNm(p_star_kPa=95.0, p_valle_kPa=91.96, b_valle_m=0.26) == pytest.approx(91.96 * 0.26**2 / 2)


def test_momento_pressione_2_kNm_p_star_greater_than_p_valle_branch():
    """p* > pvalle (3rd branch of the sheet's IF, p* > 0 and p* > pvalle)."""
    m2 = fond_valle.momento_pressione_2_kNm(p_star_kPa=120.0, p_valle_kPa=91.9612, b_star_m=0.5, b_valle_m=0.26)
    assert m2 == pytest.approx(0.5 * (120.0 - 91.9612) * 0.26 * 0.26 / 3)


def test_momento_pressione_2_kNm_matches_golden_str1_and_sisma1():
    m2_str1 = fond_valle.momento_pressione_2_kNm(p_star_kPa=83.79995787901117, p_valle_kPa=91.9612, b_star_m=0.0, b_valle_m=0.26)
    assert m2_str1 == pytest.approx(0.18389921174544896, rel=1e-5)
    m2_sisma1 = fond_valle.momento_pressione_2_kNm(
        p_star_kPa=92.72774288915225, p_valle_kPa=110.06910233431626, b_star_m=1.6502723847813994, b_valle_m=0.26
    )
    assert m2_sisma1 == pytest.approx(0.3907586328310288, rel=1e-6)


def test_momento_autopeso_kNm_is_negative_counter_moment():
    m_fond = fond_valle.momento_autopeso_kNm(gamma_g_muro=1.0, s_fond_m=0.3, gamma_cls_kN_m3=25, b_valle_m=0.26)
    assert m_fond == pytest.approx(-0.2535, rel=1e-6)
    assert m_fond < 0
