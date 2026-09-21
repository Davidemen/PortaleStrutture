"""Unit tests for periodi_spettro (NTC 2018 §3.2.3.2.1 corner periods TB/TC/TD)."""
import pytest

from strutture.shared.ntc_site_seismic.periodi_spettro import periodi_spettro

pytestmark = pytest.mark.unit


def test_periodi_spettro_golden_values():
    result = periodi_spettro(cc=1.42718050386463, tc_star_s=0.272, ag_g=0.098)
    assert result.tc == pytest.approx(0.388193, rel=1e-5)
    assert result.tb == pytest.approx(0.129398, rel=1e-5)
    assert result.td == pytest.approx(1.992, rel=1e-6)


def test_tb_is_one_third_of_tc():
    result = periodi_spettro(cc=1.05, tc_star_s=0.35, ag_g=0.15)
    assert result.tb == pytest.approx(result.tc / 3.0)
