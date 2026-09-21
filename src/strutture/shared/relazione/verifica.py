"""Structural and numeric self-consistency checks over a `relazione` (docs/architecture-phase2.md
§4): every formula parses, every identifier is explained by `valori` (no missing, no unused),
and every displayed number reproduces its own formula. Used by the test harness
(`tests/shared/relazione/harness.py`) and as a direct debug assertion wherever a tool builds its
`relazione.py` — the harness additionally cross-checks against the tool's output model, which
`problemi_traccia` alone (tool-agnostic) cannot do.
"""
from collections.abc import Iterator

from .modelli import Passo, Traccia
from .notazione import Cmp, Fn, Id, Neg, Nodo, NotazioneError, Op, Par, analizza, simbolo_identificatore
from .valuta import valuta

TOLLERANZA_RELATIVA = 1e-6
TOLLERANZA_ASSOLUTA = 1e-9


def problemi_traccia(tracce: tuple[Traccia, ...]) -> tuple[str, ...]:
    """Every internal-consistency problem found across `tracce`, as Italian sentences prefixed
    `<titolo>/<simbolo>: `. An empty tuple means every trace is coherent."""
    problemi: list[str] = []
    for traccia in tracce:
        for passo in traccia.passi:
            problemi += [f"{traccia.titolo}/{passo.simbolo}: {p}" for p in _problemi_passo(passo)]
    return tuple(problemi)


def _problemi_passo(passo: Passo) -> tuple[str, ...]:
    try:
        ast = analizza(passo.formula)
    except NotazioneError as errore:
        return (f"formula non valida: {errore.messaggio} (posizione {errore.posizione})",)
    problemi = list(_problemi_identificatori(ast, passo))
    problemi += _problemi_numerici(ast, passo)
    return tuple(problemi)


def _problemi_identificatori(ast: Nodo, passo: Passo) -> Iterator[str]:
    usati = {simbolo_identificatore(nodo) for nodo in _identificatori(ast)}
    dichiarati = {v.simbolo for v in passo.valori}
    for mancante in sorted(usati - dichiarati):
        yield f"identificatore {mancante!r} usato nella formula ma assente da valori"
    for inutilizzato in sorted(dichiarati - usati):
        yield f"identificatore {inutilizzato!r} presente in valori ma non usato nella formula"


def _problemi_numerici(ast: Nodo, passo: Passo) -> list[str]:
    valori = {v.simbolo: v.valore for v in passo.valori}
    unita = {v.simbolo: v.unita for v in passo.valori if v.unita}
    try:
        if isinstance(ast, Cmp):
            return _problemi_confronto(ast, passo, valori, unita)
        return _problemi_risultato(ast, passo, valori, unita)
    except NotazioneError as errore:
        return [f"valutazione fallita: {errore.messaggio}"]


def _problemi_risultato(ast: Nodo, passo: Passo, valori: dict[str, float], unita: dict[str, str]) -> list[str]:
    if passo.esito:
        return ["esito impostato ma la formula non è un confronto"]
    atteso = passo.scala * valuta(ast, valori, unita)
    if _vicino(atteso, passo.risultato):
        return []
    return [f"risultato={passo.risultato} non coerente con scala*valuta(formula)={atteso}"]


def _problemi_confronto(ast: Cmp, passo: Passo, valori: dict[str, float], unita: dict[str, str]) -> list[str]:
    problemi = []
    if not passo.clausola:
        problemi.append("passo di verifica senza clausola")
    if not passo.esito:
        problemi.append("confronto senza esito")
    sinistra_attesa = passo.scala * valuta(ast.a, valori, unita)
    if not _vicino(sinistra_attesa, passo.risultato):
        problemi.append(f"risultato={passo.risultato} non coerente con scala*valuta(lato sinistro)={sinistra_attesa}")
    if passo.esito:
        atteso = "soddisfatta" if bool(valuta(ast, valori, unita)) else "non soddisfatta"
        if passo.esito != atteso:
            problemi.append(f"esito={passo.esito!r} non coerente con la valutazione ({atteso!r})")
    return problemi


def _vicino(a: float, b: float) -> bool:
    return abs(a - b) <= TOLLERANZA_ASSOLUTA + TOLLERANZA_RELATIVA * abs(b)


def _identificatori(nodo: Nodo) -> Iterator[Id]:
    if isinstance(nodo, Id):
        yield nodo
    elif isinstance(nodo, Neg | Par):
        yield from _identificatori(nodo.a)
    elif isinstance(nodo, Fn):
        for argomento in nodo.args:
            yield from _identificatori(argomento)
    elif isinstance(nodo, Op | Cmp):
        yield from _identificatori(nodo.a)
        yield from _identificatori(nodo.b)
