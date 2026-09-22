"""Bundle immutabile dei risultati intermedi di pilastro-rettangolare/circolare, condiviso dai due
`tool_*.py` per restare entro il limite di dimensione dei moduli (regola dura 12 di CLAUDE.md).
Non contiene lo schizzo: quello resta calcolato nel modulo del tool per permettere il monkeypatch
di `disegna_schizzo` nei test (`tests/members/ca_pilastri/test_schizzo.py`)."""
from dataclasses import dataclass

from strutture.shared.report import Check

from .models import (
    ArmaturaMinimaResult,
    CompressioneResult,
    ConfinamentoResult,
    FlessioneResult,
    GeometriaResult,
    RegoleResult,
    SnellezzaResult,
    TaglioResult,
)
from .models import DettagliResult as _DettagliResult


@dataclass(frozen=True)
class NucleoPilastro:
    """Tutti i risultati di calcolo tranne materiali (già disponibili prima) e schizzo (calcolato
    dopo, nel modulo del tool)."""

    geometria: GeometriaResult
    armatura_minima: ArmaturaMinimaResult
    taglio: TaglioResult
    flessione: FlessioneResult
    compressione: CompressioneResult
    confinamento: ConfinamentoResult
    snellezza: SnellezzaResult
    dettagli: _DettagliResult
    regole: RegoleResult
    checks: tuple[Check, ...]
