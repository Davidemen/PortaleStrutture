"""Tokenizer + recursive-descent (Pratt-style) parser: notation string -> AST.

Whitelist grammar only (docs/architecture-phase2.md §2): numbers, identifiers (Latin/Greek,
ASCII Greek names normalised: `alpha` -> `α`, `gamma_c` -> `γ_c`), the operators `^` (right-assoc),
unary `-`, `*` `/`, `+` `-`, and comparisons `<= >= < > =` (at most ONE, at the top level only),
grouping `( )`, and calls to the fixed function list below. No assignment, no strings, no
attribute access, no other calls: any other input token is rejected with its source position.

AST nodes are frozen dataclasses whose field names already match the wire format of `ast_json.py`
(`name`/`args` for `Fn`, `op`/`a`/`b` for `Op`/`Cmp`), so serialisation is a direct, bug-resistant
one-to-one mapping. Parsing is purely functional: every rule takes `(token, i)` and returns
`(nodo, i_successivo)` — no shared mutable parser state.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Num:
    v: float


@dataclass(frozen=True)
class Id:
    base: str
    sub: str = ""


@dataclass(frozen=True)
class Neg:
    a: Nodo


@dataclass(frozen=True)
class Par:
    a: Nodo


@dataclass(frozen=True)
class Op:
    op: str  # '+' '-' '*' '/' '^'
    a: Nodo
    b: Nodo


@dataclass(frozen=True)
class Fn:
    name: str
    args: tuple[Nodo, ...]


@dataclass(frozen=True)
class Cmp:
    op: str  # '<=' '>=' '<' '>' '='
    a: Nodo
    b: Nodo


type Nodo = Num | Id | Neg | Par | Op | Fn | Cmp


def simbolo_identificatore(nodo: Id) -> str:
    """The `valori`/`unita` lookup key for an `Id` node: `base` alone, or `base_sub` when there
    is a subscript — the same shape as the notation source (`A_s`) and the UI `symbol` hint."""
    return f"{nodo.base}_{nodo.sub}" if nodo.sub else nodo.base


class NotazioneError(ValueError):
    """A rejected notation string, with the source character position of the problem."""

    def __init__(self, messaggio: str, posizione: int):
        super().__init__(f"{messaggio} (posizione {posizione})")
        self.messaggio = messaggio
        self.posizione = posizione


FUNZIONI_UN_ARGOMENTO = ("sqrt", "abs", "sin", "cos", "tan", "atan", "exp", "ln", "log10")
FUNZIONI_MULTI_ARGOMENTO = ("min", "max")
FUNZIONI_AMMESSE = frozenset(FUNZIONI_UN_ARGOMENTO + FUNZIONI_MULTI_ARGOMENTO)

_GRECO_ASCII = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "zeta": "ζ",
    "eta": "η", "theta": "θ", "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ",
    "nu": "ν", "xi": "ξ", "omicron": "ο", "pi": "π", "rho": "ρ", "sigma": "σ",
    "tau": "τ", "upsilon": "υ", "phi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
}

_LETTERA = r"A-Za-zΑ-Ωα-ω"
_NUM_RE = re.compile(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")
# Subscript: comma-separated components (`Rd,x`), each REQUIRING at least one letter/digit/prime
# right after its comma — so a comma with nothing-but-a-separator after it (`V_Rd,1, V_Rd,2`,
# `max(a_1,a_2)`) is never swallowed into the identifier: the trailing comma is left for the
# tokenizer to read next as the "," token (function-argument / list separator).
_SOTTOSCRITTO = rf"[{_LETTERA}0-9']+(?:,[{_LETTERA}0-9']+)*"
_ID_RE = re.compile(rf"[{_LETTERA}][{_LETTERA}0-9']*(?:_{_SOTTOSCRITTO})?")
_CMP_DUE_CARATTERI = ("<=", ">=")


@dataclass(frozen=True)
class _Token:
    tipo: str  # "num" "id" "op" "cmp" "(" ")" "," "eof"
    testo: str
    pos: int


def analizza(sorgente: str) -> Nodo:
    """Parse a notation string into its AST. Raises `NotazioneError` with the position of the
    first unparseable token (empty input rejects at position 0)."""
    token = _tokenizza(sorgente)
    nodo, i = _confronto(token, 0)
    if token[i].tipo != "eof":
        raise NotazioneError(f"token inatteso {token[i].testo!r}", token[i].pos)
    return nodo


def _tokenizza(sorgente: str) -> tuple[_Token, ...]:
    trovati: list[_Token] = []
    i, n = 0, len(sorgente)
    while i < n:
        carattere = sorgente[i]
        if carattere.isspace():
            i += 1
            continue
        numero = _NUM_RE.match(sorgente, i)
        identificatore = None if numero else _ID_RE.match(sorgente, i)
        if numero or identificatore:
            match = numero or identificatore
            trovati.append(_Token("num" if numero else "id", match.group(), i))
            i = match.end()
            continue
        due = sorgente[i : i + 2]
        if due in _CMP_DUE_CARATTERI:
            trovati.append(_Token("cmp", due, i))
            i += 2
            continue
        if carattere in "<>=":
            trovati.append(_Token("cmp", carattere, i))
        elif carattere in "+-*/^":
            trovati.append(_Token("op", carattere, i))
        elif carattere in "(),":
            trovati.append(_Token(carattere, carattere, i))
        else:
            raise NotazioneError(f"carattere inatteso {carattere!r}", i)
        i += 1
    trovati.append(_Token("eof", "", n))
    return tuple(trovati)


def _normalizza_base(base: str) -> str:
    """ASCII Greek names -> Unicode Greek letter, keeping any trailing digits/primes: `phi'` -> `φ'`."""
    lettere = base.rstrip("'0123456789")
    suffisso = base[len(lettere) :]
    greco = _GRECO_ASCII.get(lettere.lower())
    return f"{greco}{suffisso}" if greco else base


def _scomponi_identificatore(testo: str) -> tuple[str, str]:
    base, _, sub = testo.partition("_")
    return _normalizza_base(base), sub


def _attendi(token: tuple[_Token, ...], i: int, tipo: str) -> int:
    if token[i].tipo != tipo:
        trovato = token[i].testo or "fine della formula"
        raise NotazioneError(f"atteso {tipo!r}, trovato {trovato!r}", token[i].pos)
    return i + 1


def _confronto(token: tuple[_Token, ...], i: int) -> tuple[Nodo, int]:
    """Top-level rule only: at most one comparison, applied to two arithmetic operands."""
    sinistra, i = _somma(token, i)
    if token[i].tipo == "cmp":
        op = token[i].testo
        destra, i = _somma(token, i + 1)
        return Cmp(op=op, a=sinistra, b=destra), i
    return sinistra, i


def _somma(token: tuple[_Token, ...], i: int) -> tuple[Nodo, int]:
    sinistra, i = _termine(token, i)
    while token[i].tipo == "op" and token[i].testo in ("+", "-"):
        op = token[i].testo
        destra, i = _termine(token, i + 1)
        sinistra = Op(op=op, a=sinistra, b=destra)
    return sinistra, i


def _termine(token: tuple[_Token, ...], i: int) -> tuple[Nodo, int]:
    sinistra, i = _unario(token, i)
    while token[i].tipo == "op" and token[i].testo in ("*", "/"):
        op = token[i].testo
        destra, i = _unario(token, i + 1)
        sinistra = Op(op=op, a=sinistra, b=destra)
    return sinistra, i


def _unario(token: tuple[_Token, ...], i: int) -> tuple[Nodo, int]:
    if token[i].tipo == "op" and token[i].testo == "-":
        operando, i = _unario(token, i + 1)
        return Neg(a=operando), i
    return _potenza(token, i)


def _potenza(token: tuple[_Token, ...], i: int) -> tuple[Nodo, int]:
    base, i = _primario(token, i)
    if token[i].tipo == "op" and token[i].testo == "^":
        # Right-associative; the exponent itself may start with a unary minus (`10^-3`) without
        # parentheses — conventional calculator/engineering notation — while `-2^2` (a LEADING
        # minus in front of the whole power) still parses as `-(2^2)`, handled by `_unario` above.
        esponente, i = _unario(token, i + 1)
        return Op(op="^", a=base, b=esponente), i
    return base, i


def _primario(token: tuple[_Token, ...], i: int) -> tuple[Nodo, int]:
    corrente = token[i]
    if corrente.tipo == "num":
        return Num(v=float(corrente.testo)), i + 1
    if corrente.tipo == "(":
        interno, i = _somma(token, i + 1)
        i = _attendi(token, i, ")")
        return Par(a=interno), i
    if corrente.tipo == "id":
        if token[i + 1].tipo == "(":
            return _chiamata(token, i)
        base, sub = _scomponi_identificatore(corrente.testo)
        return Id(base=base, sub=sub), i + 1
    if corrente.tipo == "eof":
        raise NotazioneError("espressione mancante", corrente.pos)
    raise NotazioneError(f"token inatteso {corrente.testo!r}", corrente.pos)


def _chiamata(token: tuple[_Token, ...], i: int) -> tuple[Fn, int]:
    nome = token[i]
    if nome.testo not in FUNZIONI_AMMESSE:
        raise NotazioneError(f"funzione sconosciuta {nome.testo!r}", nome.pos)
    i = _attendi(token, i + 1, "(")
    argomenti: tuple[Nodo, ...] = ()
    if token[i].tipo != ")":
        argomento, i = _somma(token, i)
        argomenti = (argomento,)
        while token[i].tipo == ",":
            argomento, i = _somma(token, i + 1)
            argomenti = (*argomenti, argomento)
    i = _attendi(token, i, ")")
    _valida_arita(nome.testo, argomenti, nome.pos)
    return Fn(name=nome.testo, args=argomenti), i


def _valida_arita(nome: str, argomenti: tuple[Nodo, ...], pos: int) -> None:
    if nome in FUNZIONI_UN_ARGOMENTO and len(argomenti) != 1:
        raise NotazioneError(f"{nome} richiede esattamente un argomento", pos)
    if nome in FUNZIONI_MULTI_ARGOMENTO and len(argomenti) < 2:
        raise NotazioneError(f"{nome} richiede almeno due argomenti", pos)
