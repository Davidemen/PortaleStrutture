import pytest

from strutture.members.ca_fessurazione.verifica import utilizzo, verificato

pytestmark = pytest.mark.unit


def test_utilizzo():
    assert utilizzo(agente=4.5, limite=22.41) == pytest.approx(0.200803, rel=1e-5)


def test_utilizzo_rejects_non_positive_limite():
    with pytest.raises(ValueError, match="limite"):
        utilizzo(agente=1, limite=0)


@pytest.mark.parametrize(("agente", "limite", "atteso"), [(4.5, 22.41, True), (30, 22.41, False), (22.41, 22.41, False)])
def test_verificato(agente, limite, atteso):
    assert verificato(agente, limite) is atteso
