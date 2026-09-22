"""Verified restatement of the `geo-cedimento-elastico-timoshenko-goodier` formulas for "Sviluppo
dei calcoli" (docs/architecture-phase2.md §6, wave-2/3 adoption). Pure function of the tool's own
validated inputs and already-computed output; the calculation code of this package is never
touched — see `relazione_tg_fattori.py`/`relazione_tg_cedimento.py` for which package module each
restates. This tool declares no `Check` (a settlement result compared by the engineer against a
project-specific admissible value, same as `geo-cedimento-edometrico`); coverage is instead the two
highlighted outputs (`ΔH_centro`, `ΔH_bordo`) and every intermediate that feeds them. Standard mode
only (`execute(..., con_relazione=True)` never calls it with `legacy_compat=True`)."""
from strutture.shared.relazione import Traccia

from .models_tg import TimoshenkoGoodierInput, TimoshenkoGoodierOutput
from .relazione_tg_cedimento import traccia_cedimento
from .relazione_tg_fattori import traccia_fattori


def relazione_timoshenko_goodier(inputs: TimoshenkoGoodierInput, output: TimoshenkoGoodierOutput) -> tuple[Traccia, ...]:
    return (traccia_fattori(inputs, output), traccia_cedimento(inputs, output))
