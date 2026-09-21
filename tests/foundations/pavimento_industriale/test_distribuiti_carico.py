"""Unit tests for `carico_distribuito` (spec 'pav-carichi-distribuiti' steps 1-3)."""
import pytest

from strutture.foundations.pavimento_industriale.distribuiti_carico import carico_distribuito


@pytest.mark.unit
def test_carico_distribuito_matches_golden_case() -> None:
    result = carico_distribuito(0, 2600, 1.3, 1.5, 0.9)
    assert result.g_kN_m2 == pytest.approx(0.0)
    assert result.q_kN_m2 == pytest.approx(26.0)
    assert result.q_slu_kN_m2 == pytest.approx(39.0)
    assert result.q_sle_freq_kN_m2 == pytest.approx(23.4)


@pytest.mark.unit
def test_carico_distribuito_combines_permanent_and_variable() -> None:
    result = carico_distribuito(1000, 2000, 1.3, 1.5, 0.7)
    assert result.g_kN_m2 == pytest.approx(10.0)
    assert result.q_kN_m2 == pytest.approx(20.0)
    assert result.q_slu_kN_m2 == pytest.approx(10.0 * 1.3 + 20.0 * 1.5)
    assert result.q_sle_freq_kN_m2 == pytest.approx(10.0 + 20.0 * 0.7)
