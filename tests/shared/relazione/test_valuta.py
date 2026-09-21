"""`valuta` evaluates a parsed AST against a symbol -> value map (docs/architecture-phase2.md §2)."""
import math

import pytest

from strutture.shared.relazione.notazione import NotazioneError, analizza
from strutture.shared.relazione.valuta import valuta

pytestmark = pytest.mark.unit


def test_arithmetic_precedence_and_grouping():
    assert valuta(analizza("A_s * f_yd * (d - 0.4 * x)"), {"A_s": 1570, "f_yd": 391.3, "d": 450, "x": 98.2}) == pytest.approx(
        1570 * 391.3 * (450 - 0.4 * 98.2)
    )


def test_power_and_unary_minus():
    assert valuta(analizza("-2^2"), {}) == -4
    assert valuta(analizza("2^-2"), {}) == pytest.approx(0.25)  # unary minus allowed in the exponent


def test_comparison_returns_bool():
    assert valuta(analizza("M_Ed / M_Rd <= 1"), {"M_Ed": 214.0, "M_Rd": 252.3}) is True
    assert valuta(analizza("M_Ed / M_Rd <= 1"), {"M_Ed": 300.0, "M_Rd": 252.3}) is False


def test_unknown_identifier_raises_notazione_error():
    with pytest.raises(NotazioneError):
        valuta(analizza("a + b"), {"a": 1})


@pytest.mark.parametrize("nome,atteso", [("sqrt", math.sqrt(9)), ("abs", 4.0), ("exp", math.exp(2)), ("ln", math.log(2)), ("log10", math.log10(100))])
def test_single_argument_functions(nome, atteso):
    valori = {"sqrt": {"x": 9}, "abs": {"x": -4}, "exp": {"x": 2}, "ln": {"x": 2}, "log10": {"x": 100}}[nome]
    assert valuta(analizza(f"{nome}(x)"), valori) == pytest.approx(atteso)


def test_min_and_max():
    assert valuta(analizza("min(a,b,c)"), {"a": 3, "b": 1, "c": 2}) == 1
    assert valuta(analizza("max(a,b,c)"), {"a": 3, "b": 1, "c": 2}) == 3


def test_sin_uses_radians_by_default():
    assert valuta(analizza("sin(x)"), {"x": math.pi / 2}) == pytest.approx(1.0)


def test_sin_uses_degrees_when_argument_unit_is_degree_symbol():
    assert valuta(analizza("sin(theta)"), {"θ": 90}, {"θ": "°"}) == pytest.approx(1.0)


def test_cos_degrees_vs_radians_give_different_results_for_the_same_numeral():
    radianti = valuta(analizza("cos(x)"), {"x": 60})
    gradi = valuta(analizza("cos(x)"), {"x": 60}, {"x": "°"})
    assert radianti != pytest.approx(gradi)
    assert gradi == pytest.approx(math.cos(math.radians(60)))


def test_degree_unit_only_applies_to_a_bare_identifier_argument():
    """`sin(theta + 0)` is a computed sub-expression, not a bare identifier: always radians,
    even if `theta` itself is tagged degrees in the units map."""
    valore = valuta(analizza("sin(theta + 0)"), {"θ": math.pi / 2}, {"θ": "°"})
    assert valore == pytest.approx(math.sin(math.pi / 2))
