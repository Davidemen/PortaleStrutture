"""Evaluate a notation AST against a map of identifier values (docs/architecture-phase2.md §2).

`sin`, `cos`, `tan` and `atan` take their argument in DEGREES when that argument is a bare
identifier whose unit (from the `unita` map, keyed like `valori`) is `"°"`; radians otherwise
(including whenever the argument is not a single identifier — a computed sub-expression has no
unit of its own to look up). `atan`'s argument is itself a ratio, so in practice this only ever
fires for `sin`/`cos`/`tan`; it is checked uniformly for all four functions per the architecture
brief, so a future identifier-in-degrees argument to `atan` is handled too.
"""
import math
from collections.abc import Callable, Mapping

from .notazione import Cmp, Fn, Id, Neg, Nodo, NotazioneError, Num, Op, Par, simbolo_identificatore

GRADO = "°"
_TRIGONOMETRICHE = frozenset({"sin", "cos", "tan", "atan"})

_FUNZIONI_UN_ARGOMENTO: dict[str, Callable[[float], float]] = {
    "sqrt": math.sqrt, "abs": abs, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "atan": math.atan, "exp": math.exp, "ln": math.log, "log10": math.log10,
}
_FUNZIONI_MULTI_ARGOMENTO: dict[str, Callable[[list[float]], float]] = {"min": min, "max": max}

_OPERATORI = {
    "+": lambda a, b: a + b, "-": lambda a, b: a - b, "*": lambda a, b: a * b,
    "/": lambda a, b: a / b, "^": lambda a, b: a**b,
}
_CONFRONTI = {
    "<=": lambda a, b: a <= b, ">=": lambda a, b: a >= b, "<": lambda a, b: a < b,
    ">": lambda a, b: a > b, "=": lambda a, b: a == b,
}


def valuta(ast: Nodo, valori: Mapping[str, float], unita: Mapping[str, str] | None = None) -> float | bool:
    """Evaluate `ast` with `valori` (symbol -> value); an identifier missing from `valori` raises
    `NotazioneError`. Returns a `bool` for a `Cmp` node, a `float` otherwise."""
    unita = unita or {}
    try:
        return _valuta_nodo(ast, valori, unita)
    except KeyError as errore:
        raise NotazioneError(f"identificatore sconosciuto: {errore.args[0]!r}", -1) from errore


def _valuta_nodo(nodo: Nodo, valori: Mapping[str, float], unita: Mapping[str, str]) -> float | bool:
    if isinstance(nodo, Num):
        return nodo.v
    if isinstance(nodo, Id):
        simbolo = simbolo_identificatore(nodo)
        if simbolo not in valori:
            raise KeyError(simbolo)
        return valori[simbolo]
    if isinstance(nodo, Neg):
        return -_valuta_nodo(nodo.a, valori, unita)
    if isinstance(nodo, Par):
        return _valuta_nodo(nodo.a, valori, unita)
    if isinstance(nodo, Op):
        return _OPERATORI[nodo.op](_valuta_nodo(nodo.a, valori, unita), _valuta_nodo(nodo.b, valori, unita))
    if isinstance(nodo, Cmp):
        return _CONFRONTI[nodo.op](_valuta_nodo(nodo.a, valori, unita), _valuta_nodo(nodo.b, valori, unita))
    return _valuta_funzione(nodo, valori, unita)


def _valuta_funzione(nodo: Fn, valori: Mapping[str, float], unita: Mapping[str, str]) -> float:
    argomenti = [_valuta_nodo(arg, valori, unita) for arg in nodo.args]
    if nodo.name in _FUNZIONI_MULTI_ARGOMENTO:
        return _FUNZIONI_MULTI_ARGOMENTO[nodo.name](argomenti)
    (valore,) = argomenti
    if nodo.name in _TRIGONOMETRICHE and _argomento_in_gradi(nodo.args[0], unita):
        valore = math.radians(valore)
    return _FUNZIONI_UN_ARGOMENTO[nodo.name](valore)


def _argomento_in_gradi(argomento: Nodo, unita: Mapping[str, str]) -> bool:
    return isinstance(argomento, Id) and unita.get(simbolo_identificatore(argomento)) == GRADO
