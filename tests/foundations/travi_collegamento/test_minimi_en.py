"""Unit tests for the EN sheet's three minimum checks (armatura longitudinale, geometria, staffe)."""
import pytest

from strutture.foundations.travi_collegamento.armatura_minima_en import armatura_minima_en
from strutture.foundations.travi_collegamento.geometria_minima_en import geometria_minima_en
from strutture.foundations.travi_collegamento.staffe_minime_en import staffe_minime_en


@pytest.mark.unit
def test_armatura_minima_en_golden() -> None:
    result = armatura_minima_en(180000, 1608.5)
    assert result.rho_b_mm2 == pytest.approx(1440)
    assert result.verifica.passed


@pytest.mark.unit
def test_armatura_minima_en_fails_with_few_bars() -> None:
    result = armatura_minima_en(180000, 100.53)
    assert not result.verifica.passed


@pytest.mark.unit
def test_geometria_minima_en_golden() -> None:
    result = geometria_minima_en(400, 450, 3)
    assert result.bw_min_mm == 250
    assert result.hw_min_mm == 400
    assert result.verifica_base.passed
    assert result.verifica_altezza.passed


@pytest.mark.unit
def test_geometria_minima_en_more_than_three_floors_raises_hw_min() -> None:
    result = geometria_minima_en(400, 450, 5)
    assert result.hw_min_mm == 500
    assert not result.verifica_altezza.passed  # H=450mm < hw,min=500mm once N.floors > 3


@pytest.mark.unit
def test_geometria_minima_en_taller_section_passes_more_floors() -> None:
    result = geometria_minima_en(400, 500, 5)
    assert result.hw_min_mm == 500
    assert result.verifica_altezza.passed


@pytest.mark.unit
def test_geometria_minima_en_fails_narrow_section() -> None:
    result = geometria_minima_en(200, 450, 3)
    assert not result.verifica_base.passed


@pytest.mark.unit
def test_staffe_minime_en_golden() -> None:
    result = staffe_minime_en(400, 450, 40, 10, 2, 200, 90, 24.9, 450)
    assert result.d_mm == pytest.approx(410)
    assert result.pmax_mm == pytest.approx(307.5, rel=1e-4)
    assert result.rho_min == pytest.approx(0.000887109, rel=1e-4)
    assert result.rho == pytest.approx(0.0019635, rel=1e-4)
    assert result.verifica.passed


@pytest.mark.unit
def test_staffe_minime_en_fails_with_wide_spacing() -> None:
    result = staffe_minime_en(400, 450, 40, 10, 2, 900, 90, 24.9, 450)
    assert not result.verifica.passed
