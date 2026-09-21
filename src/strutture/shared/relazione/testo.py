"""AST -> plain text with Italian typography (docs/architecture-phase2.md §1/§2/§5): decimal
comma, "·" for `*`, "−" (U+2212) for both unary and binary minus, "≤ ≥" for comparisons. Used for
the `title`/accessible-name fallback of the MathML rendering (browser) and for any future
plain-text export (DOCX). Also composes the printed three-line equation (§5) — formula,
substituted values, result — directly from a `Passo`, the same text a human reads when reviewing
a trace without a browser.
"""
import re
from collections.abc import Callable, Mapping
from math import floor, log10

from .modelli import Passo, Traccia
from .notazione import Cmp, Fn, Id, Neg, Nodo, Num, Op, Par, analizza, simbolo_identificatore
from .valuta import valuta

MENO = "−"  # U+2212 MINUS SIGN, not the ASCII hyphen
CIFRE_SIGNIFICATIVE_DEFAULT = 4
_CONFRONTI_TESTO = {"<=": "≤", ">=": "≥", "<": "<", ">": ">", "=": "="}
_SIMBOLI_OPERATORE = {"+": " + ", "-": f" {MENO} ", "*": "·", "/": " / ", "^": "^"}

UNITA_ADIMENSIONALE = "-"  # the UI hint for "no unit": never printed
_APICI = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")

_RenderNumero = Callable[[Num], str]
_RenderIdentificatore = Callable[[Id], str]


def ast_a_testo(nodo: Nodo) -> str:
    """Symbolic rendering: identifiers and literal numbers as written in the source notation,
    never evaluated (`sostituzione_a_testo` below does that)."""
    return _rendi(nodo, numero=_numero_letterale_a_testo, identificatore=_identificatore_a_testo)


def sostituzione_a_testo(nodo: Nodo, valori: Mapping[str, float], cifre_significative: int = CIFRE_SIGNIFICATIVE_DEFAULT) -> str:
    """The same AST with every identifier replaced by its formatted numeric value from `valori`
    (keyed like `valuta.valuta`: `base` or `base_sub`)."""

    def _valore_identificatore(nodo_id: Id) -> str:
        return valore_a_testo(valori[simbolo_identificatore(nodo_id)], cifre_significative)

    return _rendi(nodo, numero=_numero_letterale_a_testo, identificatore=_valore_identificatore)


def valore_a_testo(valore: float, cifre_significative: int = CIFRE_SIGNIFICATIVE_DEFAULT) -> str:
    """Italian-formatted number, `cifre_significative` significant digits, negative values
    parenthesised (mirrors the browser's `format.js`)."""
    testo = _numero_a_cifre_significative(abs(valore), cifre_significative)
    return f"({MENO}{testo})" if valore < 0 else testo


def passo_a_testo(passo: Passo) -> str:
    """The three-line equation of §5: `simbolo = formula`, `= sostituzione`, `= risultato unità`
    (a check step instead shows `= risultato op limite` and the esito word)."""
    ast = analizza(passo.formula)
    valori = {v.simbolo: v.valore for v in passo.valori}
    riga1 = f"{passo.simbolo} = {_con_fattore(ast_a_testo(ast), ast, passo.scala)}"
    if passo.clausola:
        riga1 = f"{riga1}    {passo.clausola}"
    riga2 = f"= {_con_fattore(sostituzione_a_testo(ast, valori), ast, passo.scala)}"
    riga3 = _riga_risultato(passo, ast, valori)
    return f"{riga1}\n{riga2}\n{riga3}"


def traccia_a_testo(traccia: Traccia) -> str:
    """A full `Traccia` section: title, then every `Passo` (see `passo_a_testo`), blank-line separated."""
    corpo = "\n\n".join(passo_a_testo(passo) for passo in traccia.passi)
    return f"{traccia.titolo}\n{'=' * len(traccia.titolo)}\n\n{corpo}"


def fattore_a_testo(scala: float) -> str:
    """The display factor of a `Passo` as it is printed: "10⁻³" for a power of ten (N -> kN,
    Nmm -> kNm), the plain number otherwise; "" when there is none."""
    if scala == 1.0:
        return ""
    esponente = round(_log10(scala))
    if abs(scala - 10.0 ** esponente) <= 1e-12 * abs(scala):
        return "10" + str(esponente).translate(_APICI)
    return valore_a_testo(scala)


def _log10(valore: float) -> float:
    return log10(valore) if valore > 0 else 0.5  # a non-positive factor is never a power of ten


def _con_fattore(espressione: str, ast: Nodo, scala: float) -> str:
    """`espressione·10⁻³`: the unit conversion is part of the printed equation, which must stay true
    as written (`v·b_w·d` alone is newtons). A sum/difference/comparison operand is parenthesised
    first; a comparison keeps its factor on the left operand only (that is what `risultato` is)."""
    fattore = fattore_a_testo(scala)
    if not fattore:
        return espressione
    if isinstance(ast, Cmp):
        sinistra, _, destra = espressione.partition(f" {_CONFRONTI_TESTO[ast.op]} ")
        return f"{_con_fattore(sinistra, ast.a, scala)} {_CONFRONTI_TESTO[ast.op]} {destra}"
    serve_parentesi = isinstance(ast, Neg) or (isinstance(ast, Op) and ast.op in "+-")
    return f"({espressione})·{fattore}" if serve_parentesi else f"{espressione}·{fattore}"


_ESPONENTE_UNITA = re.compile(r"([a-zA-Zα-ωΑ-Ω])([234])(?![a-zA-Z0-9])")


def unita_a_testo(unita: str) -> str:
    """"mm2" -> "mm²", "kN/m3" -> "kN/m³" (same rule as the browser's format.js `formatUnit`)."""
    return _ESPONENTE_UNITA.sub(lambda m: m.group(1) + m.group(2).translate(_APICI), unita)


def _riga_risultato(passo: Passo, ast: Nodo, valori: Mapping[str, float]) -> str:
    if not passo.esito:
        unita = f" {unita_a_testo(passo.unita)}" if passo.unita and passo.unita != UNITA_ADIMENSIONALE else ""
        return f"= {valore_a_testo(passo.risultato)}{unita}"
    assert isinstance(ast, Cmp)  # `esito` is non-empty iff `formula` is a top-level comparison
    unita_map = {v.simbolo: v.unita for v in passo.valori if v.unita}
    limite = valuta(ast.b, valori, unita_map)
    simbolo_op = _CONFRONTI_TESTO[ast.op]
    return f"= {valore_a_testo(passo.risultato)} {simbolo_op} {valore_a_testo(float(limite))}  ({passo.esito})"


def _identificatore_a_testo(nodo_id: Id) -> str:
    return simbolo_identificatore(nodo_id)


def _numero_letterale_a_testo(numero: Num) -> str:
    testo = repr(numero.v).removesuffix(".0")
    return testo.replace(".", ",")


def _numero_a_cifre_significative(valore: float, cifre: int) -> str:
    if valore == 0:
        return "0"
    grezzo = f"{valore:.{cifre}g}"
    if "e" in grezzo or "E" in grezzo:
        # beyond the `g` format's range: still `cifre` significant digits, in plain positional notation
        # (3859521.93 -> "3860000", never the float's own twelve digits; 1.23456e-4 -> "0.0001235")
        decimali = max(cifre - 1 - floor(log10(abs(valore))), 0)
        arrotondato = round(valore, cifre - 1 - floor(log10(abs(valore))))
        grezzo = f"{arrotondato:.{decimali}f}"
    if "." in grezzo:
        grezzo = grezzo.rstrip("0").rstrip(".")
    return grezzo.replace(".", ",")


def _rendi(nodo: Nodo, *, numero: _RenderNumero, identificatore: _RenderIdentificatore) -> str:
    if isinstance(nodo, Num):
        return numero(nodo)
    if isinstance(nodo, Id):
        return identificatore(nodo)
    if isinstance(nodo, Neg):
        return f"{MENO}{_rendi(nodo.a, numero=numero, identificatore=identificatore)}"
    if isinstance(nodo, Par):
        return f"({_rendi(nodo.a, numero=numero, identificatore=identificatore)})"
    if isinstance(nodo, Fn):
        return _rendi_funzione(nodo, numero=numero, identificatore=identificatore)
    if isinstance(nodo, Op):
        sinistra = _rendi(nodo.a, numero=numero, identificatore=identificatore)
        destra = _rendi(nodo.b, numero=numero, identificatore=identificatore)
        return f"{sinistra}{_SIMBOLI_OPERATORE[nodo.op]}{destra}"
    sinistra = _rendi(nodo.a, numero=numero, identificatore=identificatore)
    destra = _rendi(nodo.b, numero=numero, identificatore=identificatore)
    return f"{sinistra} {_CONFRONTI_TESTO[nodo.op]} {destra}"


def _rendi_funzione(nodo: Fn, *, numero: _RenderNumero, identificatore: _RenderIdentificatore) -> str:
    testi = [_rendi(arg, numero=numero, identificatore=identificatore) for arg in nodo.args]
    if nodo.name == "abs":
        return f"|{testi[0]}|"
    return f"{nodo.name}({', '.join(testi)})"
