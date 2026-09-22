"""Verified restatement of `neve-carico-falda`/`neve-accumulo` for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6, wave-3 adoption). Pure function of each tool's own validated
inputs and already-computed output; the calculation code is never touched — see each
`relazione_*.py` module's own docstring for which package module it restates."""
from strutture.shared.relazione import Traccia

from .models import AccumuloInput, AccumuloOutput, CaricoFaldaInput, CaricoFaldaOutput
from .relazione_accumulo import traccia_lunghezza_e_coefficienti, traccia_progetto
from .relazione_comune import traccia_carico_al_suolo
from .relazione_falda import traccia_falde

TITOLO_CARICO_AL_SUOLO = "Carico neve al suolo e coefficiente di esposizione"


def relazione_carico_falda(inputs: CaricoFaldaInput, output: CaricoFaldaOutput) -> tuple[Traccia, ...]:
    """2 Traccia, 9-11 passi: carico al suolo (q_sk, C_E, C_t) e carico di progetto sulla copertura."""
    return (
        traccia_carico_al_suolo(
            zona=output.zona, altitude_m=inputs.as_m, qsk_val=output.qsk,
            topografia=inputs.topografia, ce_val=output.ce, ct_val=inputs.ct, titolo=TITOLO_CARICO_AL_SUOLO,
        ),
        traccia_falde(inputs, output),
    )


def relazione_accumulo(inputs: AccumuloInput, output: AccumuloOutput) -> tuple[Traccia, ...]:
    """3 Traccia, 10 passi: carico al suolo, geometria/coefficienti dell'accumulo, carichi di progetto."""
    return (
        traccia_carico_al_suolo(
            zona=output.zona, altitude_m=inputs.as_m, qsk_val=output.qsk,
            topografia=inputs.topografia, ce_val=output.ce, ct_val=inputs.ct, titolo=TITOLO_CARICO_AL_SUOLO,
        ),
        traccia_lunghezza_e_coefficienti(inputs, output),
        traccia_progetto(inputs, output),
    )
