"""Parser tests (docs/architecture-phase2.md §2): precedence, associativity, identifier shapes,
Greek normalisation, the function whitelist, and every rejection case named in the brief, each
checked for the reported source position."""
import pytest

from strutture.shared.relazione.notazione import (
    Cmp,
    Fn,
    Id,
    Neg,
    NotazioneError,
    Num,
    Op,
    Par,
    analizza,
)

pytestmark = pytest.mark.unit


def test_multiplication_binds_tighter_than_addition():
    assert analizza("a + b * c") == Op("+", Id("a"), Op("*", Id("b"), Id("c")))


def test_power_binds_tighter_than_unary_minus():
    """`-2^2` is `-(2^2)` = -4, the usual mathematical convention."""
    assert analizza("-2^2") == Neg(Op("^", Num(2.0), Num(2.0)))


def test_power_is_right_associative():
    assert analizza("2^3^2") == Op("^", Num(2.0), Op("^", Num(3.0), Num(2.0)))


def test_unary_minus_binds_looser_than_power_but_tighter_than_product():
    """`2*-3^2` = `2 * -(3^2)` = `2 * (-9)`: the right operand of `*` is parsed as `unary`."""
    assert analizza("2*-3^2") == Op("*", Num(2.0), Neg(Op("^", Num(3.0), Num(2.0))))


def test_unary_minus_allowed_directly_in_an_exponent():
    """`10^-3` (engineering notation) needs no parentheses around the exponent."""
    assert analizza("10^-3") == Op("^", Num(10.0), Neg(Num(3.0)))


def test_explicit_parentheses_are_kept_in_the_ast():
    assert analizza("(a + b) * c") == Op("*", Par(Op("+", Id("a"), Id("b"))), Id("c"))


def test_division_and_subtraction_left_associative():
    assert analizza("a - b - c") == Op("-", Op("-", Id("a"), Id("b")), Id("c"))
    assert analizza("a / b / c") == Op("/", Op("/", Id("a"), Id("b")), Id("c"))


@pytest.mark.parametrize(
    "sorgente,atteso",
    [
        ("A_s", Id("A", "s")),
        ("M_Rd,x", Id("M", "Rd,x")),
        ("c'_k", Id("c'", "k")),
        ("f_yd", Id("f", "yd")),
        ("d", Id("d")),
    ],
)
def test_identifiers_with_subscripts_commas_and_primes(sorgente, atteso):
    assert analizza(sorgente) == atteso


def test_subscript_with_comma_and_prime_together():
    assert analizza("σ_c,max") == Id("σ", "c,max")


@pytest.mark.parametrize(
    "sorgente,atteso",
    [
        ("alpha", Id("α")),
        ("gamma_c", Id("γ", "c")),
        ("phi'_k", Id("φ'", "k")),
        ("sigma_cp", Id("σ", "cp")),
    ],
)
def test_ascii_greek_names_are_normalised(sorgente, atteso):
    assert analizza(sorgente) == atteso


def test_unicode_greek_identifier_passes_through_unchanged():
    assert analizza("σ") == Id("σ")
    assert analizza("η") == Id("η")


@pytest.mark.parametrize("nome", ["sqrt", "min", "max", "abs", "sin", "cos", "tan", "atan", "exp", "ln", "log10"])
def test_every_whitelisted_function_parses(nome):
    argomenti = "a,b" if nome in ("min", "max") else "a"
    nodo = analizza(f"{nome}({argomenti})")
    assert isinstance(nodo, Fn) and nodo.name == nome


def test_comparison_operators_and_exactly_one_at_top_level():
    for op in ("<=", ">=", "<", ">", "="):
        assert analizza(f"a {op} b") == Cmp(op, Id("a"), Id("b"))


@pytest.mark.parametrize(
    "sorgente,posizione",
    [
        ("bogus(1)", 0),
        ("2x", 1),
        ("a b", 2),
        ('a."b"', 1),
        ('"5"', 0),
        ("x := 5", 2),
        ("0 <= x <= 1", 7),
        ("(1 + 2", 6),
        ("1 + 2)", 5),
        ("", 0),
    ],
)
def test_rejections_report_the_offending_position(sorgente, posizione):
    with pytest.raises(NotazioneError) as errore:
        analizza(sorgente)
    assert errore.value.posizione == posizione


def test_attribute_access_rejected():
    with pytest.raises(NotazioneError):
        analizza("a.b")


def test_sqrt_requires_exactly_one_argument():
    with pytest.raises(NotazioneError):
        analizza("sqrt(a,b)")
    with pytest.raises(NotazioneError):
        analizza("sqrt()")


def test_min_requires_at_least_two_arguments():
    with pytest.raises(NotazioneError):
        analizza("min(a)")


def test_comma_subscript_identifier_adjacent_to_the_argument_separator_is_not_ambiguous():
    """The subscript charset contains ',' (`M_Rd,x`), so a naive greedy subscript match would
    swallow a directly-following argument-separator comma too (`max(V_Rd,1, V_Rd,2)`). The
    subscript grammar requires a real component (letter/digit/prime) after every internal comma,
    so a comma followed by whitespace (the customary "a, b" spacing — nothing-but-a-separator) is
    correctly left over for the tokenizer to read next as the "," argument separator."""
    assert analizza("max(V_Rd,1, V_Rd,2)") == Fn("max", (Id("V", "Rd,1"), Id("V", "Rd,2")))
    assert analizza("max(a_1, a_2)") == Fn("max", (Id("a", "1"), Id("a", "2")))


def test_comma_subscript_identifier_immediately_touching_the_next_argument_is_still_ambiguous():
    """Without ANY separating space (`a_1,a_2`), a single leading letter of the next argument is
    itself a valid subscript character and is genuinely indistinguishable from more subscript —
    this is a known limitation of a whitespace-insensitive tokenizer; the customary "a, b" spacing
    (space after the comma) used throughout this codebase's formulas avoids it entirely."""
    with pytest.raises(NotazioneError):
        analizza("max(a_1,a_2)")
