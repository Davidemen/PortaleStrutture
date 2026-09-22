"""Verified restatement of the `muro-sostegno` formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6, wave 2 adoption). Pure function of the tool's own validated
inputs and already-computed output; the calculation code of this package is never touched — see
each `relazione_*.py` module's own docstring for which package module it restates and which
intermediate (not exposed by `MuroSostegnoOutput`) it reads straight from the package's own step
functions.

8 combinazioni per verification group (docs/architecture-phase2.md §5, "many-rows tools trace the
GOVERNING row only"): `relazione_comune.combo_governante_stabilita` picks the one combination that
governs BOTH ribaltamento and scorrimento (the smallest safety margin of either), reused by the
spinta/pesi, ribaltamento-scorrimento and pressioni traces; the three reinforcement groups and the
optional bearing-capacity check use their OWN `combo_governante` (already on the output). Every one
of the 16 ribaltamento/scorrimento `Check`s still gets its own `Passo` (the formula, shown once in
full for the governing row, restated with each other row's own numbers — `relazione_stabilita.py`).
"""
from strutture.shared.relazione import Traccia

from .models import MuroSostegnoInput, MuroSostegnoOutput
from .relazione_armatura_fondazione import traccia_armatura_fondazione_monte, traccia_armatura_fondazione_valle
from .relazione_armatura_paramento import traccia_armatura_paramento
from .relazione_capacita_portante import traccia_capacita_portante
from .relazione_geometria import traccia_geometria
from .relazione_pressioni import traccia_pressioni
from .relazione_spinta import traccia_spinta
from .relazione_stabilita import traccia_stabilita


def relazione(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> tuple[Traccia, ...]:
    tracce = (
        traccia_geometria(inputs, output),
        traccia_spinta(inputs, output),
        traccia_stabilita(inputs, output),
        traccia_pressioni(output),
        traccia_armatura_paramento(inputs, output),
        traccia_armatura_fondazione_valle(inputs, output),
        traccia_armatura_fondazione_monte(inputs, output),
    )
    capacita_portante = traccia_capacita_portante(inputs, output)
    if capacita_portante is not None:
        tracce = (*tracce, capacita_portante)
    return tracce
