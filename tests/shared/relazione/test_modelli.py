"""`Valore` / `Passo` / `Traccia` are frozen and carry the shape of docs/architecture-phase2.md §1."""
import pytest
from pydantic import ValidationError

from strutture.shared.relazione.modelli import Passo, Traccia, Valore

pytestmark = pytest.mark.unit


def _passo(**overrides: object) -> Passo:
    base = {
        "simbolo": "M_Rd",
        "formula": "A_s * f_yd * d",
        "valori": (Valore(simbolo="A_s", valore=1570.0, unita="mm2"),),
        "risultato": 252.3,
        "unita": "kNm",
    }
    return Passo(**{**base, **overrides})


def test_passo_is_frozen():
    passo = _passo()
    with pytest.raises(ValidationError):
        passo.risultato = 0.0


def test_traccia_holds_passi_in_order():
    traccia = Traccia(titolo="Resistenza a taglio", passi=(_passo(simbolo="a"), _passo(simbolo="b")))
    assert [p.simbolo for p in traccia.passi] == ["a", "b"]


def test_traccia_requires_at_least_one_passo():
    with pytest.raises(ValidationError):
        Traccia(titolo="Vuota", passi=())


def test_traccia_rejects_more_than_forty_passi():
    with pytest.raises(ValidationError):
        Traccia(titolo="Troppo lunga", passi=tuple(_passo(simbolo=f"x{i}") for i in range(41)))


def test_esito_only_accepts_the_two_italian_literals_or_empty():
    with pytest.raises(ValidationError):
        _passo(esito="qualcosa")
    assert _passo(esito="soddisfatta").esito == "soddisfatta"
    assert _passo(esito="non soddisfatta").esito == "non soddisfatta"
    assert _passo().esito == ""


def test_scala_defaults_to_one():
    assert _passo().scala == 1.0
