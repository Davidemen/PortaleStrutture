"""Unit tests for `snellezza_en` (EN slenderness check, EC2-style formula)."""
import pytest

from strutture.foundations.travi_collegamento.snellezza_en import snellezza_en
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_snellezza_en_golden() -> None:
    result = snellezza_en(400, 450, 5000, 1, 122.31, 180000, 14.11, 1608.5, 391.304)
    assert result.omega == pytest.approx(0.247819, rel=1e-4)
    assert result.lambda_ == pytest.approx(43.3013, rel=1e-5)
    assert result.lambda_lim == pytest.approx(54.6145, rel=1e-4)
    assert result.verifica.passed
    assert result.tasso_lavoro == pytest.approx(0.792853, rel=1e-4)


@pytest.mark.unit
def test_snellezza_en_rejects_zero_ned() -> None:
    """NEd=0 (soil A, α=0) makes λlim's denominator zero (#DIV/0! in the sheet)."""
    with pytest.raises(CalcError):
        snellezza_en(400, 450, 5000, 1, 0.0, 180000, 14.11, 1608.5, 391.304)
