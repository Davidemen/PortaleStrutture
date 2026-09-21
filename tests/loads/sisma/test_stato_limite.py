import pytest

from strutture.loads.sisma.stato_limite import is_stato_limite_uls


@pytest.mark.unit
@pytest.mark.parametrize("stato_limite", ["SLV", "SLC", "slv", "slc", "SlV"])
def test_is_uls_true_for_ultimate_states(stato_limite: str):
    assert is_stato_limite_uls(stato_limite) is True


@pytest.mark.unit
@pytest.mark.parametrize("stato_limite", ["SLO", "SLD", "slo", "sld"])
def test_is_uls_false_for_serviceability_states(stato_limite: str):
    assert is_stato_limite_uls(stato_limite) is False
