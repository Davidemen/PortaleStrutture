"""Verified restatement of `ca-sezione-dominio-mn` formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6, wave 2/3 adoption). Pure function of the tool's own validated
inputs and already-computed output; the calculation code of this package is never touched.
Rebuilds the `Sezione` from `inputs` (`sezione_builder.costruisci_sezione`, the same pure step
`compose.run` itself calls) to reach intermediates the output never exposes (`N_max`/`N_min`, the
exact `M_Rd` at the governing row) — exactly as the architecture brief allows.

The M-N/Mx-My domains (`dominio_x`, `dominio_y`) are a CHART, not a trace (§6): this `relazione`
covers materials, the geometric summary, the domain's axial extremes and the governing row's
utilisation only, covering the tool's single `Check` and both highlighted outputs (`A_s`, `ρ`)."""
from strutture.shared.relazione import Traccia
from strutture.shared.sezione_ca.geometria import bounding_box

from .models_input import SezioneMnInput
from .models_output import SezioneMnOutput
from .relazione_geometria import traccia_dominio_assiale, traccia_geometria, traccia_materiali
from .relazione_governante import traccia_governante
from .sezione_builder import costruisci_sezione


def relazione(inputs: SezioneMnInput, output: SezioneMnOutput) -> tuple[Traccia, ...]:
    sezione = costruisci_sezione(inputs)
    xmin, ymin, xmax, ymax = bounding_box(sezione.contorno)
    h_x_mm, h_y_mm = ymax - ymin, xmax - xmin
    return (
        traccia_materiali(inputs, output.materiali),
        traccia_geometria(inputs, output.geometria),
        traccia_dominio_assiale(output.materiali, output.geometria, sezione),
        traccia_governante(sezione, output.governante, h_x_mm, h_y_mm),
    )
