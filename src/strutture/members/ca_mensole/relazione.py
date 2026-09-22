"""Verified restatement of `ca-mensola-tozza` formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6, wave 2/3 adoption). Pure function of the tool's own validated
inputs and already-computed output; the calculation code of this package is never touched — see
each `relazione_*.py` module's own docstring for which package module it restates.

17 passi across 5 `Traccia` (within the 8-30 target of docs/architecture-phase2.md §6), covering
all 3 `Check` this tool emits (`verifica.py`) and its highlighted output (`P_R`)."""
from strutture.shared.relazione import Traccia

from .models import MensolaTozzaInput, MensolaTozzaOutput
from .relazione_armatura import traccia_armatura
from .relazione_capacita import traccia_capacita, traccia_verifiche
from .relazione_materiali_geometria import traccia_geometria, traccia_materiali


def relazione(inputs: MensolaTozzaInput, output: MensolaTozzaOutput) -> tuple[Traccia, ...]:
    return (
        traccia_materiali(inputs, output.materiali),
        traccia_geometria(inputs, output.geometria),
        traccia_armatura(inputs, output.armature, output.materiali.fyd_MPa),
        traccia_capacita(inputs, output.materiali, output.geometria, output.armature, output.capacita),
        traccia_verifiche(inputs, output.capacita, output.armature),
    )
