"""Verified restatement of `vento-pressione` for "Sviluppo dei calcoli" (docs/architecture-phase2.md
§6, wave-3 adoption). Pure function of the tool's own validated inputs and already-computed output;
the calculation code is never touched — see each `relazione_*.py` module's own docstring for which
package module it restates.

13 passi across 3 `Traccia`: zona vento e categoria di esposizione (6 lookup), velocità di
riferimento (4) e pressione cinetica/coefficiente di esposizione (3), covering the tool's 3
highlighted outputs (v_r, c_e(H), p(H))."""
from strutture.shared.relazione import Traccia

from .models import VentoPressioneInput, VentoPressioneOutput
from .relazione_pressione import traccia_pressione
from .relazione_velocita import traccia_velocita_di_riferimento
from .relazione_zona import traccia_zona_e_categoria


def relazione(inputs: VentoPressioneInput, output: VentoPressioneOutput) -> tuple[Traccia, ...]:
    return (
        traccia_zona_e_categoria(inputs, output),
        traccia_velocita_di_riferimento(inputs, output),
        traccia_pressione(inputs, output),
    )
