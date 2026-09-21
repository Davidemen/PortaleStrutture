"""Unit tests for `compressione` (Nc,Rd + verifica + tasso di lavoro)."""
import pytest

from strutture.foundations.travi_collegamento.compressione import compressione


@pytest.mark.unit
def test_compressione_golden_passes() -> None:
    result = compressione(160000, 14.11, 122.31)
    assert result.ncrd_kN == pytest.approx(2257.6, rel=1e-5)
    assert result.verifica.passed
    assert result.tasso_lavoro == pytest.approx(0.054177, rel=1e-4)


@pytest.mark.unit
def test_compressione_fails_when_demand_exceeds_capacity() -> None:
    result = compressione(40000, 14.11, 2249.1)
    assert not result.verifica.passed
    assert result.tasso_lavoro > 1
