"""Unit tests for `minimi_ntc` (d, pmax, Ast,min, Ast, verifica)."""
import pytest

from strutture.foundations.travi_collegamento.minimi_ntc import minimi_ntc


@pytest.mark.unit
def test_minimi_ntc_golden() -> None:
    result = minimi_ntc(400, 400, 40, 10, 2, 125)
    assert result.d_mm == pytest.approx(360)
    assert result.pmax_mm == pytest.approx(288)
    assert result.ast_min_mm2_per_m == pytest.approx(600)
    assert result.ast_mm2 == pytest.approx(157.08, rel=1e-4)
    assert result.verifica.passed


@pytest.mark.unit
def test_minimi_ntc_fails_with_wide_spacing() -> None:
    result = minimi_ntc(400, 400, 40, 10, 2, 400)
    assert not result.verifica.passed


@pytest.mark.unit
def test_minimi_ntc_pmax_absolute_cap() -> None:
    """pmax caps at 1000/3 mm even for a very deep section (0.8d would otherwise exceed it)."""
    result = minimi_ntc(400, 2000, 40, 10, 2, 125)
    assert result.pmax_mm == pytest.approx(1000.0 / 3.0)
