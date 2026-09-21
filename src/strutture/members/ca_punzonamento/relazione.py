"""Verified restatement of the ca-punzonamento formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md, EN 1992-1-1 §6.4 punching + §9.4.3 detailing). The calculation code of
this package is never touched: every value below is either read straight from `PunzonamentoOutput`
or recomputed via the package's own step functions / shared EC2 helpers for an intermediate the
output model does not expose (§0). Split into `relazione_*.py` modules (this file only orchestrates)
because the tool has two independent verifications — punching without reinforcement, always traced,
and the reinforcement design that follows only when it fails (§6 "punching reinforcement if
present") — each with several `Check` entries and a highlighted output to restate.

`beta` (the eccentricity factor, EN 1992-1-1 §6.4.3(6)) is looked up once here, exactly like
`compose.run` does, and threaded through every trace that needs it, instead of every submodule
repeating the same table lookup."""
from strutture.shared.relazione import Traccia
from strutture.shared.tables import exact_lookup

from .models import PunzonamentoInput, PunzonamentoOutput
from .relazione_armatura import traccia_armatura
from .relazione_cls import traccia_perimetro_critico, traccia_rho_k
from .relazione_faccia import traccia_faccia_pilastro
from .tables import POSIZIONE_BETA


def relazione(inputs: PunzonamentoInput, output: PunzonamentoOutput) -> tuple[Traccia, ...]:
    """8-25 steps on the tool's example (no reinforcement needed); more when the reinforcement
    design trace is also present, covering every `Check` and both highlighted outputs
    ("v_Ed,i/v_Rd,i" always, "V_Ed/V_Rd" only when reinforcement is required)."""
    beta = exact_lookup(POSIZIONE_BETA, inputs.posizione)
    traccia_perimetro, v_c = traccia_perimetro_critico(inputs, output, beta)
    tracce = (
        traccia_faccia_pilastro(inputs, output, beta),
        traccia_rho_k(inputs, output),
        traccia_perimetro,
    )
    return tracce + traccia_armatura(inputs, output, beta, v_c)
