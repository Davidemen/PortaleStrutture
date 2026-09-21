"""Verified restatement of the `ca-trave-rettangolare` formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6, wave 1 adoption). Pure function of the tool's own validated
inputs and already-computed output; the calculation code of this package is never touched — see
each `relazione_*.py` module's own docstring for which package module it restates and which
intermediate (not exposed by `TraveRettangolareOutput`) it reads straight from the package's own
step functions.

25 passi across 7 `Traccia` (within the 8-25 target of docs/architecture-phase2.md §6), covering
every `Check` this tool's `run()` emits (`tool.py::_checks`) and every highlighted output
(`M_Rd`, `M_Ed/M_Rd`, `V_Rd`): geometria (3), limiti di armatura (4 Check), duttilità sismica (3
Check), flessione (2 valori + 2 Check), taglio (3 valori + 1 Check), capacity design (1 Check),
stato limite di esercizio (1 valore + 3-4 Check). The trace describes the STANDARD mode only
(`execute(..., con_relazione=True)` never calls it with `legacy_compat=True`, see
`strutture.shared.tool._con_relazione`).
"""
from strutture.shared.relazione import Traccia

from .models import TraveRettangolareInput, TraveRettangolareOutput
from .relazione_armatura import traccia_duttilita_sismica, traccia_limiti_armatura
from .relazione_flessione import traccia_flessione
from .relazione_geometria import traccia_geometria
from .relazione_sle import traccia_sle
from .relazione_taglio import traccia_capacity_design, traccia_taglio


def relazione(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> tuple[Traccia, ...]:
    return (
        traccia_geometria(inputs, output),
        traccia_limiti_armatura(inputs, output),
        traccia_duttilita_sismica(inputs, output),
        traccia_flessione(inputs, output),
        traccia_taglio(inputs, output),
        traccia_capacity_design(inputs, output),
        traccia_sle(inputs, output),
    )
