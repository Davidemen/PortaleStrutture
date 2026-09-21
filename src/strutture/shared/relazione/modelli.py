"""Frozen pydantic models for a "relazione di calcolo" trace (docs/architecture-phase2.md §1).

A `Traccia` is one section of "Sviluppo dei calcoli" (e.g. "Resistenza a taglio"); it carries a
tuple of `Passo`, each one displayed equation an engineer would write by hand. `Passo.formula` is
notation (see `notazione.py`), never a pre-evaluated string: the harness (`tests/shared/relazione/
harness.py`) parses and evaluates every formula against `valori` to catch drift between the
displayed formula and the code that produced `risultato`.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_PASSI_PER_TRACCIA = 40


class Valore(BaseModel):
    """One identifier of a `Passo.formula`, with the value it took in this trace."""

    model_config = ConfigDict(frozen=True)

    simbolo: str  # "f_yd" — same notation as the UI `symbol` hint
    valore: float
    unita: str = ""
    descrizione: str = ""  # Italian, optional ("tensione di snervamento di progetto")


class Passo(BaseModel):
    """One displayed equation: `simbolo = formula`, substituted with `valori`, equal to `risultato`."""

    model_config = ConfigDict(frozen=True)

    simbolo: str  # left-hand side, "M_Rd"; for a check: the utilisation symbol, "η"
    formula: str  # notation (notazione.py): "A_s * f_yd * (d - 0.4 * x)"; a check: "M_Ed / M_Rd <= 1"
    valori: tuple[Valore, ...]  # every identifier of `formula`, in order of first appearance
    risultato: float  # value of the left-hand side (for a check: of the left operand)
    unita: str = ""
    clausola: str = ""  # "NTC2018 §4.1.2.3.4.2"; REQUIRED for check steps
    nota: str = ""  # Italian, one sentence, optional
    esito: Literal["", "soddisfatta", "non soddisfatta"] = ""  # non-empty iff `formula` is a comparison
    scala: float = 1.0  # display factor result = scala * eval (unit conversion, e.g. 1e-6 for Nmm -> kNm)


class Traccia(BaseModel):
    """One section of "Sviluppo dei calcoli"."""

    model_config = ConfigDict(frozen=True)

    titolo: str  # Italian, "Resistenza a flessione"
    passi: tuple[Passo, ...] = Field(min_length=1, max_length=MAX_PASSI_PER_TRACCIA)
