"""Verified restatement of `fond-plinto-isolato` (docs/architecture-phase2.md §6 "wave 1"): the
calculation code is never touched, this only restates its formulas from the tool's own validated
inputs and already-computed output. STANDARD mode only (`legacy_compat=False`) — `execute()` never
calls `relazione` for `legacy_compat=True` runs (docs §1), and the legacy branches compute
different formulas anyway (`docs/divergences/plinti-isolati.md`).

One Traccia per governing combination (docs §5, "many-rows tools trace the GOVERNING row only"):
`output.governante` (the SIGMA-max row) for self-weights/eccentricities/pressures/the "Portanza"
check; separately, whichever row actually governs `mu_scorrimento_minimo`/`mu_ribaltamento_minimo`
(often a DIFFERENT row on a multi-combination table, see `relazione_sicurezza.py`); the ULS-family
pressure envelope for the cantilever moment/reinforcement; and, only when the "Terreno" input block
is filled, the row governing `capacita_portante.governante` for the Annex D bearing-capacity check.
Each Traccia names its own governing combination in its title."""
from strutture.shared.relazione import Traccia

from .input import PlintoIsolatoInput
from .models import PlintoIsolatoOutput
from .relazione_armatura import traccia_momento_e_armatura
from .relazione_azioni import traccia_eccentricita_e_pressioni, traccia_pesi_propri_e_carico
from .relazione_capacita_portante import traccia_capacita_portante
from .relazione_helpers import trova_reazione
from .relazione_sicurezza import traccia_ribaltamento, traccia_scorrimento


def relazione(inputs: PlintoIsolatoInput, output: PlintoIsolatoOutput) -> tuple[Traccia, ...]:
    """8-25 steps grouped by governing combination; see module docstring for which row each
    section traces. `Traccia` sections whose quantity has no defined value for these inputs
    (no shear/overturning demand anywhere, "Terreno" block empty) are omitted."""
    governante = output.governante
    reazione = trova_reazione(inputs.reazioni, governante.nodo, governante.combo)
    tracce: tuple[Traccia, ...] = (
        traccia_pesi_propri_e_carico(inputs, governante, reazione),
        traccia_eccentricita_e_pressioni(inputs, governante, reazione),
    )
    for possibile in (
        traccia_scorrimento(inputs, output),
        traccia_ribaltamento(inputs, output),
    ):
        if possibile is not None:
            tracce = (*tracce, possibile)
    tracce = (*tracce, traccia_momento_e_armatura(inputs, output))
    annesso_d = traccia_capacita_portante(inputs, output)
    if annesso_d is not None:
        tracce = (*tracce, annesso_d)
    return tracce
