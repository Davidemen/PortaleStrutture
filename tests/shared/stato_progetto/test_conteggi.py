"""conta: aggregate counts for the project head (§25.3)."""
import pytest

from strutture.shared.stato_progetto.conteggi import conta


def _voce(**over):
    base = {"da_ricalcolare": False, "provvisorio": False, "provvisorio_origine": False, "motivi": []}
    return {**base, **over}


@pytest.mark.unit
def test_basic_counts():
    stati = ["verificato", "non_verificato", "dati_modificati"]
    voci = [_voce(), _voce(da_ricalcolare=True), _voce(provvisorio=True)]
    conteggi = conta(stati, voci)
    assert conteggi.elementi == 3
    assert conteggi.verificati == 1
    assert conteggi.non_verificati == 1
    assert conteggi.dati_modificati == 1
    assert conteggi.da_ricalcolare == 1
    assert conteggi.provvisori == 1


@pytest.mark.unit
def test_controllo_rinviato_and_cicli_from_motivi():
    voci = [
        _voce(da_ricalcolare=True, motivi=[{"causa": "controllo_rinviato"}]),
        _voce(da_ricalcolare=True, motivi=[{"causa": "ciclo_origini"}]),
        _voce(),
    ]
    conteggi = conta(["verificato"] * 3, voci)
    assert conteggi.controllo_rinviato == 1
    assert conteggi.cicli_origini == 1
