"""Verified restatement of `vento-cpe-rettangolare` for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6, wave-3 adoption). Pure function of the tool's own validated inputs
and already-computed output; the calculation code is never touched.

2 `Traccia` (one per wind direction), 4-8 passi each — see `relazione_direzione.py`'s own docstring.
`VentoCpeOutput.classification` (`classification.py::classify`) is a squat/slender LABEL, not a
number, so it has no `Passo` of its own (`Passo.risultato` is a `float`); it is instead stated in
direction 2's own `Traccia` title, alongside the two h/d ratios that determine it, since it always
depends on BOTH directions together (`docs/architecture-phase2.md §6`'s "every highlight" applies to
NUMERIC highlights, the only kind `Passo`/the harness can restate — see
`tests/shared/relazione/harness.py::_campi_output`, which already skips non-numeric fields)."""
from strutture.shared.relazione import Traccia

from .models import VentoCpeInput, VentoCpeOutput
from .relazione_direzione import traccia_direzione


def relazione(inputs: VentoCpeInput, output: VentoCpeOutput) -> tuple[Traccia, ...]:
    traccia1 = traccia_direzione(1, "vento ⟂ al lato b", inputs.h, inputs.d, "d", output.dir1)
    traccia2 = traccia_direzione(2, "vento ⟂ al lato d", inputs.h, inputs.b, "b", output.dir2)
    return traccia1, _con_classificazione(traccia2, output.classification)


def _con_classificazione(traccia: Traccia, classification: str) -> Traccia:
    """Appende la classificazione complessiva (entrambe le direzioni) al titolo della seconda
    Traccia, l'unico punto in cui entrambi i rapporti h/d sono già stati resi."""
    return traccia.model_copy(update={"titolo": f'{traccia.titolo} — classificazione complessiva: "{classification}"'})
