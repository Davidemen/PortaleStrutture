"""Verified restatement of the `geo-cedimento-elastico-newmark` formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6, wave-2/3 adoption). Pure function of the tool's own validated
inputs and already-computed output; the calculation code of this package is never touched — see
`relazione_newmark_centro.py`/`relazione_newmark_punto.py`/`relazione_newmark_righe.py` for which
package module each restates. This tool declares no `Check` (a settlement result compared by the
engineer against a project-specific admissible value); coverage is instead the highlighted output
(`w` or `w_O`, per `modalita`) and every intermediate that feeds it. Standard mode only
(`execute(..., con_relazione=True)` never calls it with `legacy_compat=True`)."""
from strutture.shared.relazione import Traccia

from .models_newmark import NewmarkInput, NewmarkOutput
from .relazione_newmark_centro import tracce_centro
from .relazione_newmark_punto import tracce_punto


def relazione_newmark(inputs: NewmarkInput, output: NewmarkOutput) -> tuple[Traccia, ...]:
    if inputs.modalita == "CENTRO":
        return tracce_centro(inputs, output)
    return tracce_punto(inputs, output)
