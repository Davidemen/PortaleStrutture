"""Verified restatement of the `geo-cedimento-edometrico` formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6, wave-2/3 adoption). Pure function of the tool's own validated
inputs and already-computed output; the calculation code of this package is never touched — see
each `relazione_*.py` module's own docstring for which package module it restates.

This tool declares no `Check` (docs/specs/geo-cedimenti-edometrico.md: "no explicit pass/fail
check cell exists in this sheet"); coverage is instead the two highlighted outputs (`Z_crit`,
`w_ed`) and every intermediate that feeds them. Standard mode only (`execute(...,
con_relazione=True)` never calls it with `legacy_compat=True`, see
`strutture.shared.tool._con_relazione`)."""
from strutture.shared.relazione import Traccia

from .models import EdometricoInput
from .output import EdometricoOutput
from .relazione_cedimento import traccia_cedimento
from .relazione_pressione import traccia_pressione
from .relazione_profondita_critica import traccia_profondita_critica


def relazione(inputs: EdometricoInput, output: EdometricoOutput) -> tuple[Traccia, ...]:
    return (
        traccia_pressione(inputs, output),
        traccia_profondita_critica(inputs, output),
        traccia_cedimento(inputs, output),
    )
