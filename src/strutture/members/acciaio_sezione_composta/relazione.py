"""Verified restatement of the `acciaio-sezione-h-rimpiattata` formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6). Pure function of the tool's own validated inputs and
already-computed output; the calculation code of this package is never touched — see each
`relazione_*.py` module's own docstring for what it restates.

17 passi across 2 `Traccia` (within the 8-30 target of docs/architecture-phase2.md §6): area,
baricentro, momenti d'inerzia e loro rapporto rispetto al profilo base (7), moduli di resistenza
elastici/plastici e raggi d'inerzia (10). This tool declares NO `Check` (`tool.py::run` calls
`success(data, inputs)` with no `checks=`): the trace is entirely informative, plain mechanics — no
EN clause applies to a rectangle's own statics — restating every highlighted output (A, I_x, I_y).
"""
from strutture.shared.relazione import Traccia

from .models import SezioneHRimpiattataInput
from .relazione_geometria import traccia_geometria
from .relazione_moduli import traccia_moduli
from .risultati import SezioneHRimpiattataOutput


def relazione(inputs: SezioneHRimpiattataInput, output: SezioneHRimpiattataOutput) -> tuple[Traccia, ...]:
    return (
        traccia_geometria(output.elementi, output.sezione),
        traccia_moduli(inputs, output.elementi, output.sezione),
    )
