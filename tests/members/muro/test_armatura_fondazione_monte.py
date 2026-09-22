"""Unit tests for `armatura_fondazione_monte` (muro-sostegno rows 172-187), Tratto A values."""
import pytest

from strutture.members.muro import armatura_fondazione_monte as fond_monte

pytestmark = pytest.mark.unit


def test_pressione_interpolata_trapezio_branch_str1():
    p_star_star = fond_monte.pressione_interpolata_kPa(b_star_m=0.0, p_valle_kPa=91.9612, p_monte_kPa=32.3216, b_fond_m=1.9, b_monte_m=1.15)
    assert p_star_star == pytest.approx(68.41922043785222, rel=1e-6)


def test_pressione_interpolata_triangolo_above_threshold_sisma1():
    p_star_star = fond_monte.pressione_interpolata_kPa(
        b_star_m=1.6502723847813994, p_valle_kPa=110.06910233431626, p_monte_kPa=0.0, b_fond_m=1.9, b_monte_m=1.15
    )
    assert p_star_star == pytest.approx(60.04595008865089, rel=1e-6)


def test_pressione_interpolata_can_go_negative_when_b_star_below_heel_root():
    """B* < Bfond-Bmonte (heel-root threshold) still takes the interpolation branch (the sheet's
    condition is `B* > -(Bfond-Bmonte)`, always true for B*>=0), giving a negative p** — the sheet
    itself does this (see docs/divergences/muro-sostegno.md)."""
    p_star_star = fond_monte.pressione_interpolata_kPa(b_star_m=0.0425388242608519, p_valle_kPa=4270.07570510512, p_monte_kPa=0.0, b_fond_m=1.9, b_monte_m=1.15)
    assert p_star_star == pytest.approx(-71015.4272319408, rel=1e-6)


def test_pressione_interpolata_dead_else_branch_is_zero():
    """The sheet's `IF(B* > -(Bfond-Bmonte), ..., 0)` else-branch is unreachable for any physical
    geometry (B*>=0, Bmonte<Bfond always); kept for literal fidelity, tested directly."""
    p_star_star = fond_monte.pressione_interpolata_kPa(b_star_m=0.3, p_valle_kPa=100.0, p_monte_kPa=0.0, b_fond_m=0.6, b_monte_m=1.0)
    assert p_star_star == 0.0


def test_momento_pressione_kNm_matches_golden_str1_and_sisma1():
    m_p_str1 = fond_monte.momento_pressione_kNm(p_monte_kPa=32.3216, p_star_star_kPa=68.41922043785222, b_monte_m=1.15, b_fond_m=1.9, b_star_m=0.0)
    assert m_p_str1 == pytest.approx(-29.32916253777968, rel=1e-6)
    m_p_sisma1 = fond_monte.momento_pressione_kNm(
        p_monte_kPa=0.0, p_star_star_kPa=60.04595008865089, b_monte_m=1.15, b_fond_m=1.9, b_star_m=1.6502723847813994
    )
    assert m_p_sisma1 == pytest.approx(-8.111110685367406, rel=1e-6)
    assert m_p_str1 < 0
    assert m_p_sisma1 < 0


def test_momento_pressione_kNm_p_star_star_below_p_monte_branch():
    """pmonte>0 and p** <= pmonte (3rd branch of the sheet's nested IF)."""
    m_p = fond_monte.momento_pressione_kNm(p_monte_kPa=50.0, p_star_star_kPa=20.0, b_monte_m=1.15, b_fond_m=1.9, b_star_m=0.0)
    assert m_p == pytest.approx(-(20.0 * 1.15**2 / 2 + 0.5 * (50.0 - 20.0) * 1.15 * (2 * 1.15 / 3)))
    assert m_p < 0


def test_momento_terreno_kNm_matches_golden_sisma1():
    m_terr = fond_monte.momento_terreno_kNm(w_terr_kN=54.37199999999999, b_monte_m=1.15, b_fond_m=1.9, x_terr_m=1.325)
    assert m_terr == pytest.approx(31.263899999999992, rel=1e-6)


def test_momento_sovraccarico_verticale_kNm_is_zero_when_delta_is_zero():
    """δ=0 -> SV.q=SV.terr=0 in the golden case, so MEd.SV=0 regardless of the lever arm."""
    assert fond_monte.momento_sovraccarico_verticale_kNm(sv_tot_kN=0.0, x_sv_m=1.325, b_fond_m=1.9, b_monte_m=1.15) == 0.0


def test_momento_autopeso_kNm_legacy_matches_golden_str1():
    """The sheet's own value (col J): exponents swapped, reproduced only in Excel mode."""
    m_fond = fond_monte.momento_autopeso_kNm(b_monte_m=1.15, gamma_g_muro=1.3, gamma_cls_kN_m3=25, s_fond_m=0.3, legacy_compat=True)
    assert m_fond == pytest.approx(1.681875, rel=1e-6)


def test_momento_autopeso_kNm_standard_is_the_cantilever_of_projection_b_monte():
    """γG·γcls·s_fond·B_monte²/2 — the same form as the toe (armatura_fondazione_valle), found by the
    engineering proof-read of the calculation report: 1,3·25·0,3·1,15²/2 = 6,4472 kNm, 3,8× the
    sheet's 1,68 (non-conservative there, the error factor being B_monte/s_fond)."""
    m_fond = fond_monte.momento_autopeso_kNm(b_monte_m=1.15, gamma_g_muro=1.3, gamma_cls_kN_m3=25, s_fond_m=0.3)
    assert m_fond == pytest.approx(1.3 * 25 * 0.3 * 1.15**2 / 2, rel=1e-9)
    quadrata = fond_monte.momento_autopeso_kNm(b_monte_m=0.3, gamma_g_muro=1.0, gamma_cls_kN_m3=25, s_fond_m=0.3)
    assert quadrata == pytest.approx(fond_monte.momento_autopeso_kNm(b_monte_m=0.3, gamma_g_muro=1.0, gamma_cls_kN_m3=25, s_fond_m=0.3, legacy_compat=True))
