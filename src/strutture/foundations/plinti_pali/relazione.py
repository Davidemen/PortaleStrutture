"""Verified restatement of `fond-plinto-su-pali` (docs/architecture-phase2.md §6, wave 2 adoption).
The calculation code is never touched — see each `relazione_*.py` module's own docstring for which
package module it restates and which intermediate (not exposed by `PlintoSuPaliOutput`) it reads
straight from the package's own step functions. STANDARD mode only (`execute(..., con_relazione=
True)` never calls it with `legacy_compat=True`, see `strutture.shared.tool._con_relazione`).

This ONE tool composes what the architecture brief's wave-1/2 adoptions elsewhere split across
several tools (Tool-1 envelope, Tool-2 flexure, Tool-3 strut-and-tie, Tool-4 shear/punching,
docs/specs/fond-plinti-pali.md): ~33 passi across 9 Traccia, above the "8-25" sizing target of
docs/architecture-phase2.md §6 (widened for the same reason `ca_travi.relazione`'s own docstring
widens its budget to 30 — necessary coverage, here of 4 composed sub-tools' worth of Check +
highlight, not padding) — every `Check` `tool.py::_checks` can emit and all 3 highlighted outputs
(`N_max`, `η_st`, `η_v`)."""
from strutture.shared.relazione import Traccia

from .input import PlintoSuPaliInput
from .models import PlintoSuPaliOutput
from .pesi_propri import peso_proprio_kN
from .relazione_armatura_superiore import traccia_armatura_superiore
from .relazione_flessione import traccia_flessione_x, traccia_flessione_y
from .relazione_puntoni_tiranti import traccia_puntoni_tiranti
from .relazione_punzonamento import traccia_punzonamento_colonna, traccia_punzonamento_palo
from .relazione_reazioni import traccia_capacita_pali, traccia_reazioni_pali
from .relazione_taglio import traccia_taglio
from .relazione_utilizzo import traccia_utilizzo_taglio_punzonamento


def relazione(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput) -> tuple[Traccia, ...]:
    peso_kN = peso_proprio_kN(inputs.ax_m, inputs.by_m, inputs.h_plinto_m, inputs.gamma_g1, inputs.carico_aggiuntivo_kN)
    return (
        traccia_reazioni_pali(inputs, output),
        traccia_capacita_pali(output),
        traccia_flessione_x(inputs, output, peso_kN),
        traccia_flessione_y(inputs, output, peso_kN),
        traccia_armatura_superiore(inputs, output),
        traccia_puntoni_tiranti(inputs, output),
        traccia_taglio(inputs, output, peso_kN),
        traccia_punzonamento_colonna(inputs, output, peso_kN),
        traccia_punzonamento_palo(inputs, output),
        traccia_utilizzo_taglio_punzonamento(output),
    )
