"""Unit tests for `geometria_muro` (muro-sostegno rows 29-39), Tratto A golden inputs/outputs."""
import pytest

from strutture.members.muro.geometria import geometria_muro

pytestmark = pytest.mark.unit


def test_geometria_muro_tratto_a():
    result = geometria_muro(h_muro_m=2.4, s_fond_m=0.3, s_base_m=0.49, s_top_m=0.25, b_valle_m=0.26, b_monte_m=1.15)
    assert result.h_muro_tot_m == pytest.approx(2.7)
    assert result.b_fond_m == pytest.approx(1.9)
    assert result.a_muro_m2 == pytest.approx(1.458)
    assert result.x_muro_m == pytest.approx(0.661523, rel=1e-5)
    assert result.a_terr_m2 == pytest.approx(2.76)
    assert result.x_terr_m == pytest.approx(1.325)
    assert result.x_sv_m == pytest.approx(1.325)


def test_geometria_muro_rectangular_stem_centroid_is_half_base():
    """s_base == s_top -> the stem is a plain rectangle; x_muro reduces to a weighted average of
    the footing-slab and stem-rectangle centroids (the triangular correction term vanishes)."""
    result = geometria_muro(h_muro_m=2.0, s_fond_m=0.3, s_base_m=0.3, s_top_m=0.3, b_valle_m=0.3, b_monte_m=1.0)
    b_fond = 1.6
    a_fond = b_fond * 0.3
    a_stem = 2.0 * 0.3
    atteso = (a_fond * (b_fond / 2) + a_stem * (0.3 + 0.3 - 0.15)) / (a_fond + a_stem)
    assert result.x_muro_m == pytest.approx(atteso)
