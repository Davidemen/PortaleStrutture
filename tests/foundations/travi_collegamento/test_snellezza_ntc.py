"""Unit tests for `snellezza_ntc` (NTC slenderness check)."""
import pytest

from strutture.foundations.travi_collegamento.snellezza_ntc import snellezza_ntc
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_snellezza_ntc_golden() -> None:
    result = snellezza_ntc(400, 400, 5000, 1, 122.31, 160000, 14.11)
    assert result.l0_mm == pytest.approx(5000)
    assert result.i_mm == pytest.approx(115.470, rel=1e-5)
    assert result.lambda_ == pytest.approx(43.3013, rel=1e-5)
    assert result.lambda_lim == pytest.approx(107.407, rel=1e-5)
    assert result.verifica.passed
    assert result.tasso_lavoro == pytest.approx(0.403151, rel=1e-4)


@pytest.mark.unit
def test_snellezza_ntc_fails_on_long_slender_span() -> None:
    result = snellezza_ntc(400, 400, 9000, 2, 122.31, 160000, 14.11)
    assert not result.verifica.passed


@pytest.mark.unit
def test_snellezza_ntc_rejects_zero_ned() -> None:
    with pytest.raises(CalcError):
        snellezza_ntc(400, 400, 5000, 1, 0.0, 160000, 14.11)
