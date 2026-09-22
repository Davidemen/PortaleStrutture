"""testo.py: Italian typography (docs/architecture-phase2.md §1) — decimal comma, "·" for `*`,
"−" (U+2212) for minus, "≤ ≥" for comparisons; and the three-line `Passo` rendering of §5."""
import pytest

from strutture.shared.relazione.modelli import Passo, Traccia, Valore
from strutture.shared.relazione.notazione import analizza
from strutture.shared.relazione.testo import (
    ast_a_testo,
    passo_a_testo,
    sostituzione_a_testo,
    traccia_a_testo,
    valore_a_testo,
)

pytestmark = pytest.mark.unit


def test_symbolic_rendering_matches_the_architecture_brief_example():
    """docs/architecture-phase2.md §1: `"A_s·f_yd·(d − 0.4·x)"` (Italian comma applied on top)."""
    testo = ast_a_testo(analizza("A_s * f_yd * (d - 0.4 * x)"))
    assert testo == "A_s·f_yd·(d − 0,4·x)"


def test_comparison_uses_le_symbol():
    assert ast_a_testo(analizza("M_Ed / M_Rd <= 1")) == "M_Ed / M_Rd ≤ 1"


@pytest.mark.parametrize("op,simbolo", [("<=", "≤"), (">=", "≥"), ("<", "<"), (">", ">"), ("=", "=")])
def test_every_comparison_operator(op, simbolo):
    assert ast_a_testo(analizza(f"a {op} b")) == f"a {simbolo} b"


def test_unary_minus_uses_the_minus_sign_not_ascii_hyphen():
    testo = ast_a_testo(analizza("-x"))
    assert testo == "−x"
    assert "-" not in testo


def test_function_and_abs_rendering():
    assert ast_a_testo(analizza("sqrt(x)")) == "sqrt(x)"
    assert ast_a_testo(analizza("abs(x)")) == "|x|"
    assert ast_a_testo(analizza("min(a,b)")) == "min(a, b)"


def test_substitution_replaces_identifiers_with_formatted_values():
    ast = analizza("A_s * f_yd * (d - 0.4 * x)")
    testo = sostituzione_a_testo(ast, {"A_s": 1570, "f_yd": 391.3, "d": 450, "x": 98.2})
    assert testo == "1570·391,3·(450 − 0,4·98,2)"


def test_valore_a_testo_uses_four_significant_digits_and_italian_comma():
    assert valore_a_testo(252.297) == "252,3"
    assert valore_a_testo(0.0022333) == "0,002233"
    assert valore_a_testo(1005.0) == "1005"


def test_valore_a_testo_parenthesises_negative_values():
    assert valore_a_testo(-3.5) == "(−3,5)"


def _passo_flessione() -> Passo:
    return Passo(
        simbolo="M_Rd",
        formula="A_s * f_yd * (d - 0.4 * x)",
        valori=(
            Valore(simbolo="A_s", valore=1570, unita="mm2"),
            Valore(simbolo="f_yd", valore=391.3, unita="MPa"),
            Valore(simbolo="d", valore=450, unita="mm"),
            Valore(simbolo="x", valore=98.2, unita="mm"),
        ),
        risultato=252.3,
        unita="kNm",
        clausola="NTC2018 §4.1.2.3.4.2",
    )


def test_passo_a_testo_renders_the_three_lines_of_a_result_step():
    testo = passo_a_testo(_passo_flessione())
    righe = testo.splitlines()
    assert righe[0] == "M_Rd = A_s·f_yd·(d − 0,4·x)    NTC2018 §4.1.2.3.4.2"
    assert righe[1] == "= 1570·391,3·(450 − 0,4·98,2)"
    assert righe[2] == "= 252,3 kNm"


def _passo_verifica() -> Passo:
    return Passo(
        simbolo="η",
        formula="M_Ed / M_Rd <= 1",
        valori=(
            Valore(simbolo="M_Ed", valore=214.0, unita="kNm"),
            Valore(simbolo="M_Rd", valore=252.3, unita="kNm"),
        ),
        risultato=0.85,
        clausola="NTC2018 §4.1.2.3.4.2",
        esito="soddisfatta",
    )


def test_passo_a_testo_renders_a_check_step_with_esito():
    testo = passo_a_testo(_passo_verifica())
    righe = testo.splitlines()
    assert righe[2] == "= 0,85 ≤ 1  (soddisfatta)"


def test_traccia_a_testo_includes_title_and_every_passo():
    traccia = Traccia(titolo="Resistenza a flessione", passi=(_passo_flessione(), _passo_verifica()))
    testo = traccia_a_testo(traccia)
    assert testo.startswith("Resistenza a flessione\n")
    assert "M_Rd = A_s·f_yd·(d − 0,4·x)" in testo
    assert "= 0,85 ≤ 1  (soddisfatta)" in testo


# --- review refinements: dimensionless unit, visible unit conversion -------------------------------

def _passo(**overrides):
    from strutture.shared.relazione.modelli import Passo, Valore

    base = {
        "simbolo": "V_Rd", "formula": "v * b_w * d",
        "valori": (Valore(simbolo="v", valore=0.4, unita="MPa"), Valore(simbolo="b_w", valore=1000.0, unita="mm"),
                   Valore(simbolo="d", valore=450.0, unita="mm")),
        "risultato": 180.0, "unita": "kN", "scala": 1e-3,
    }
    return Passo.model_validate({**base, **overrides})


def test_the_dimensionless_unit_dash_is_not_printed() -> None:
    from strutture.shared.relazione.modelli import Valore
    from strutture.shared.relazione.testo import passo_a_testo

    testo = passo_a_testo(_passo(simbolo="k", formula="a + 1", valori=(Valore(simbolo="a", valore=0.5),), risultato=1.5, unita="-", scala=1.0))
    assert testo.splitlines()[-1] == "= 1,5"


def test_a_power_of_ten_display_factor_is_shown_on_both_lines() -> None:
    """N -> kN: the printed equation must stay true as written, `v·b_w·d` alone is 180000, not 180."""
    from strutture.shared.relazione.testo import passo_a_testo

    righe = passo_a_testo(_passo()).splitlines()
    assert righe[0] == "V_Rd = v·b_w·d·10⁻³"
    assert righe[1] == "= 0,4·1000·450·10⁻³"
    assert righe[2] == "= 180 kN"


def test_a_sum_is_parenthesised_before_the_display_factor() -> None:
    from strutture.shared.relazione.modelli import Valore
    from strutture.shared.relazione.testo import passo_a_testo

    passo = _passo(formula="a + b", valori=(Valore(simbolo="a", valore=1000.0), Valore(simbolo="b", valore=500.0)), risultato=1.5, scala=1e-3)
    assert passo_a_testo(passo).splitlines()[0] == "V_Rd = (a + b)·10⁻³"


def test_a_factor_that_is_not_a_power_of_ten_is_printed_as_a_number() -> None:
    from strutture.shared.relazione.modelli import Valore
    from strutture.shared.relazione.testo import passo_a_testo

    passo = _passo(formula="a", valori=(Valore(simbolo="a", valore=10.0),), risultato=98.0665, unita="kPa", scala=9.80665)
    assert passo_a_testo(passo).splitlines()[0] == "V_Rd = a·9,807"


# --- proof-read findings: big numbers and unit exponents -------------------------------------------

def test_a_large_value_is_rounded_to_the_significant_digits_not_printed_with_float_noise() -> None:
    from strutture.shared.relazione.testo import valore_a_testo

    assert valore_a_testo(3859521.926595) == "3860000"
    assert valore_a_testo(125000.0) == "125000"
    assert valore_a_testo(0.000123456) == "0,0001235"


def test_unit_exponents_are_typographic() -> None:
    from strutture.shared.relazione.testo import passo_a_testo

    assert passo_a_testo(_passo(unita="mm2", scala=1.0, risultato=180000.0)).splitlines()[-1] == "= 180000 mm²"
    assert passo_a_testo(_passo(unita="kN/m3", scala=1.0, risultato=180000.0)).splitlines()[-1] == "= 180000 kN/m³"


def test_the_note_of_a_step_is_rendered_as_a_fourth_line() -> None:
    """A `nota` carries the governing condition of a branch-selected formula (the proof-read of
    three waves found them invisible in the text rendering): it is part of the equation."""
    from strutture.shared.relazione.testo import passo_a_testo

    righe = passo_a_testo(_passo(nota="Valido per σ_cp/f_cd < 0,25.")).splitlines()
    assert righe[-1] == "Valido per σ_cp/f_cd < 0,25."
    assert len(passo_a_testo(_passo()).splitlines()) == 3  # no note, no fourth line
