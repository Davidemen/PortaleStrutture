"""`relazione di calcolo`: a verified restatement of a tool's formulas (docs/architecture-phase2.md).

The calculation code is never touched: an adopting tool's `relazione(inputs, output)` picks values
from its own inputs/output (and, when needed, its own step functions) and restates the formulas in
the small notation parsed here. A test harness (`tests/shared/relazione/harness.py`) parses and
evaluates every `Passo.formula` and asserts it reproduces `Passo.risultato`, so drift between a
displayed formula and the code that produced it is caught by CI, not by a reviewer's eye.
"""
from .ast_json import ast_a_json
from .modelli import MAX_PASSI_PER_TRACCIA, Passo, Traccia, Valore
from .notazione import (
    FUNZIONI_AMMESSE,
    Cmp,
    Fn,
    Id,
    Neg,
    Nodo,
    NotazioneError,
    Num,
    Op,
    Par,
    analizza,
    simbolo_identificatore,
)
from .testo import ast_a_testo, passo_a_testo, sostituzione_a_testo, traccia_a_testo, valore_a_testo
from .valuta import valuta
from .verifica import problemi_traccia

__all__ = [
    "FUNZIONI_AMMESSE",
    "MAX_PASSI_PER_TRACCIA",
    "Cmp",
    "Fn",
    "Id",
    "Neg",
    "Nodo",
    "NotazioneError",
    "Num",
    "Op",
    "Par",
    "Passo",
    "Traccia",
    "Valore",
    "analizza",
    "ast_a_json",
    "ast_a_testo",
    "passo_a_testo",
    "problemi_traccia",
    "simbolo_identificatore",
    "sostituzione_a_testo",
    "traccia_a_testo",
    "valore_a_testo",
    "valuta",
]
