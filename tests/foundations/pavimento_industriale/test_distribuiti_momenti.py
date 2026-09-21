"""Unit tests for `momenti_distribuito` (Westergaard UDL moments, spec steps 4-5)."""
import pytest

from strutture.foundations.pavimento_industriale.distribuiti_momenti import momenti_distribuito

_LAMBDA_MM1 = 0.000919499


@pytest.mark.unit
def test_momenti_distribuito_matches_golden_case() -> None:
    result = momenti_distribuito(39.0, 23.4, _LAMBDA_MM1)
    assert result.m_slu_sup_Nmm_m == pytest.approx(7758.68, rel=1e-5)
    assert result.m_slu_inf_Nmm_m == pytest.approx(7435.78, rel=1e-5)
    assert result.m_sle_freq_sup_Nmm_m == pytest.approx(4655.21, rel=1e-5)
    assert result.m_sle_freq_inf_Nmm_m == pytest.approx(4461.47, rel=1e-5)


@pytest.mark.unit
def test_top_fibre_coefficient_exceeds_bottom() -> None:
    """spec: sup coefficient 0.1682 > inf coefficient 0.1612, so sup moment > inf for the same q."""
    result = momenti_distribuito(39.0, 23.4, _LAMBDA_MM1)
    assert result.m_slu_sup_Nmm_m > result.m_slu_inf_Nmm_m
