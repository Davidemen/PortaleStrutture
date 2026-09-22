"""Verified restatement of the `acciaio-colonna-h-ec3` formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6). Pure function of the tool's own validated inputs and
already-computed output; the calculation code of this package is never touched — see each
`relazione_*.py` module's own docstring for which package module it restates and which intermediate
(not exposed by `ColonnaEc3Output`) it reads straight from the package's own step functions.

30 passi across 8 `Traccia` (within the 8-30 target of docs/architecture-phase2.md §6), covering
every one of the 11 `Check` this tool's `run()` emits (`tool.py::run`) and both highlighted outputs
(`utilizzo_yy`/`utilizzo_zz`): materiali e sezione (3 valori), instabilità per flessione semplice (6,
informativa), instabilità flesso-torsionale (3, informativa), resistenza a taglio (2 Check),
resistenza a flessione (2 Check, +0-2 se scatta la riduzione per taglio elevato), instabilità per
taglio dell'anima (1 Check + 1 soglia informativa), interazione N-My-Mz (2 Check + 3 valori tabellari),
verifiche semplificate di riscontro (4 Check + 1 valore riutilizzato). The trace describes the
STANDARD mode only (`execute(..., con_relazione=True)` never calls it with `legacy_compat=True`, see
`strutture.shared.tool._con_relazione`).
"""
from strutture.shared.relazione import Traccia

from .models import ColonnaEc3Input
from .relazione_flessione import traccia_flessione
from .relazione_instabilita_flessionale import traccia_instabilita_flessionale
from .relazione_instabilita_torsionale import traccia_instabilita_torsionale
from .relazione_interazione import traccia_interazione
from .relazione_interazione_semplificata import traccia_interazione_semplificata
from .relazione_sezione import traccia_sezione
from .relazione_taglio import traccia_taglio
from .relazione_taglio_instabilita import traccia_taglio_instabilita
from .results import ColonnaEc3Output


def relazione(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> tuple[Traccia, ...]:
    return (
        traccia_sezione(inputs, output),
        traccia_instabilita_flessionale(inputs, output),
        traccia_instabilita_torsionale(inputs, output),
        traccia_taglio(inputs, output),
        traccia_flessione(inputs, output),
        traccia_taglio_instabilita(inputs, output),
        traccia_interazione(inputs, output),
        traccia_interazione_semplificata(inputs, output),
    )
