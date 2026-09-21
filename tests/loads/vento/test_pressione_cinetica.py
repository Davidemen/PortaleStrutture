import pytest

from strutture.loads.vento.pressione_cinetica import pressione_cinetica_riferimento


@pytest.mark.unit
def test_pressione_cinetica_golden():
    assert pressione_cinetica_riferimento(25) == pytest.approx(0.390625, rel=1e-6)


@pytest.mark.unit
def test_pressione_cinetica_scala_col_quadrato_della_velocita():
    assert pressione_cinetica_riferimento(50) == pytest.approx(4 * pressione_cinetica_riferimento(25), rel=1e-9)
