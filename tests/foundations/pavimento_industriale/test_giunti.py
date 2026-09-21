"""Unit tests for `giunti` (spec 'pav-giunti' steps 1-5)."""
import pytest

from strutture.foundations.pavimento_industriale.giunti import giunti


@pytest.mark.unit
def test_giunti_matches_golden_case() -> None:
    result = giunti(20, 18, 30.9, 21.2, 1e-5, 30, 200)
    assert result.rapporto_contrazione == pytest.approx(1.11111, rel=1e-5)
    assert result.verifica_contrazione.passed is True
    assert result.l_max_contrazione_cm == pytest.approx(460.0)
    assert result.spessore_isolamento_mm == pytest.approx(40.0)
    assert result.rapporto_isolamento == pytest.approx(1.45755, rel=1e-5)
    assert result.verifica_isolamento.passed is True
    assert result.apertura_dilatazione_mm == pytest.approx(9.27, rel=1e-5)


@pytest.mark.unit
def test_verifica_fails_above_threshold() -> None:
    """Both rows use the 1.5 threshold (spec bug 3: row 39's label says 1.2 but its own formula
    tests 1.5, kept as-is -- see docs/divergences/pavimento-industriale.md)."""
    result = giunti(20, 10, 30, 20, 1e-5, 30, 200)  # 20/10 = 2.0 > 1.5
    assert result.verifica_contrazione.passed is False
    assert result.verifica_contrazione.limit == pytest.approx(1.5)
