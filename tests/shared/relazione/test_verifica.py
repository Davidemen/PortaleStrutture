"""`problemi_traccia` (docs/architecture-phase2.md §4): a coherent trace reports nothing; each
kind of drift between a formula and its displayed numbers is caught with a readable message."""
import pytest

from strutture.shared.relazione.modelli import Passo, Traccia, Valore
from strutture.shared.relazione.verifica import problemi_traccia

pytestmark = pytest.mark.unit


def _traccia_flessione(**override_passo: object) -> Traccia:
    base = {
        "simbolo": "M_Rd",
        "formula": "A_s * f_yd * d",
        "valori": (
            Valore(simbolo="A_s", valore=1570.0),
            Valore(simbolo="f_yd", valore=391.3),
            Valore(simbolo="d", valore=0.450),
        ),
        "risultato": 1570.0 * 391.3 * 0.450,
        "unita": "Nmm",
    }
    return Traccia(titolo="Resistenza a flessione", passi=(Passo(**{**base, **override_passo}),))


def test_coherent_trace_has_no_problems():
    assert problemi_traccia((_traccia_flessione(),)) == ()


def test_invalid_formula_is_reported_with_position():
    problemi = problemi_traccia((_traccia_flessione(formula="A_s * (f_yd"),))
    assert len(problemi) == 1
    assert "formula non valida" in problemi[0]
    assert "posizione" in problemi[0]


def test_missing_identifier_in_valori_is_reported():
    problemi = problemi_traccia((_traccia_flessione(formula="A_s * f_yd * d * gamma"),))
    assert any("γ" in p and "assente da valori" in p for p in problemi)


def test_unused_valore_is_reported():
    valori = (
        Valore(simbolo="A_s", valore=1570.0),
        Valore(simbolo="f_yd", valore=391.3),
        Valore(simbolo="d", valore=0.450),
        Valore(simbolo="extra", valore=1.0),
    )
    problemi = problemi_traccia((_traccia_flessione(valori=valori),))
    assert any("'extra'" in p and "non usato" in p for p in problemi)


def test_wrong_risultato_is_reported():
    problemi = problemi_traccia((_traccia_flessione(risultato=1.0),))
    assert any("non coerente con scala*valuta(formula)" in p for p in problemi)


def test_wrong_scala_is_caught_too():
    """scala is part of the checked equation: result = scala * valuta(formula)."""
    traccia = _traccia_flessione(risultato=1570.0 * 391.3 * 0.450 * 1e-6, unita="kNm", scala=1.0)
    problemi = problemi_traccia((traccia,))
    assert problemi  # scala=1.0 but risultato was computed as if scala were 1e-6


def test_correct_scala_is_accepted():
    traccia = _traccia_flessione(risultato=1570.0 * 391.3 * 0.450 * 1e-6, unita="kNm", scala=1e-6)
    assert problemi_traccia((traccia,)) == ()


def _traccia_verifica(**override_passo: object) -> Traccia:
    base = {
        "simbolo": "η",
        "formula": "M_Ed / M_Rd <= 1",
        "valori": (Valore(simbolo="M_Ed", valore=214.0), Valore(simbolo="M_Rd", valore=252.3)),
        "risultato": 214.0 / 252.3,
        "clausola": "NTC2018 §4.1.2.3.4.2",
        "esito": "soddisfatta",
    }
    return Traccia(titolo="Verifica a flessione", passi=(Passo(**{**base, **override_passo}),))


def test_coherent_check_step_has_no_problems():
    assert problemi_traccia((_traccia_verifica(),)) == ()


def test_check_step_without_clausola_is_reported():
    assert any("senza clausola" in p for p in problemi_traccia((_traccia_verifica(clausola=""),)))


def test_check_step_without_esito_is_reported():
    assert any("senza esito" in p for p in problemi_traccia((_traccia_verifica(esito=""),)))


def test_check_step_with_wrong_esito_is_reported():
    problemi = problemi_traccia((_traccia_verifica(esito="non soddisfatta"),))
    assert any("non coerente con la valutazione" in p for p in problemi)


def test_check_step_with_wrong_left_hand_risultato_is_reported():
    problemi = problemi_traccia((_traccia_verifica(risultato=0.5),))
    assert any("non coerente con scala*valuta(lato sinistro)" in p for p in problemi)


def test_esito_set_on_non_comparison_formula_is_reported():
    problemi = problemi_traccia((_traccia_flessione(esito="soddisfatta"),))
    assert any("esito impostato ma la formula non è un confronto" in p for p in problemi)
