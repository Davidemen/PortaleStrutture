import pytest

from strutture.foundations.plinti_pali.capacita_pali import capacita_compressione, capacita_trazione


@pytest.mark.unit
def test_capacita_compressione_verificata() -> None:
    result = capacita_compressione(896.06124265, 1200.0)
    assert result.domanda_kN == pytest.approx(896.06124265, rel=1e-9)
    assert result.verificato is True
    assert result.utilizzo == pytest.approx(896.06124265 / 1200.0, rel=1e-9)


@pytest.mark.unit
def test_capacita_compressione_non_verificata() -> None:
    result = capacita_compressione(1500.0, 1200.0)
    assert result.verificato is False


@pytest.mark.unit
def test_capacita_trazione_usa_il_valore_assoluto_della_domanda() -> None:
    result = capacita_trazione(-150.0, 200.0)
    assert result.domanda_kN == pytest.approx(150.0, rel=1e-9)
    assert result.verificato is True
