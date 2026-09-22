"""Verified restatement of the `fond-pavimento-industriale` formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6, wave-2/3 adoption). Pure function of the tool's own validated
inputs and already-computed output; the calculation code of this package is never touched — see
each `relazione_*.py` module's own docstring for which package module it restates. Covers all 13
`Check`s `tool.py::run` collects (6 carico distribuito + 5 carichi concentrati [already reduced to
the governing row per grandezza by `concentrati.py`'s own "many-rows result", docs/architecture-
phase2.md §5] + 2 giunti) and all 3 highlighted outputs (`l`, the distributed `TL_max`, the
concentrated `TL_max` — the latter two share the identical `symbol` hint, so one `Passo` named
`TL_max` explains both, docs/architecture-phase2.md §4). Standard mode only (`execute(...,
con_relazione=True)` never calls it with `legacy_compat=True`).

Step budget: 30 (the architecture doc's own "8-25", already widened by `ca_travi.relazione` to
"30" when a real tool's own Check count demands it): 13 mandatory Check steps + 3 highlighted-value
steps + the "interior/edge/corner" Westergaard demonstration the brief explicitly asks for leave no
slack below the high twenties once every reused intermediate (fck, fcfd, d, Ecm, W, λ, Mrd, VRd,max,
VRd,c, b) is honestly derived rather than restated as a bare literal."""
from strutture.shared.relazione import Traccia

from .armatura import ArmaturaResult
from .concentrati import ConcentratiResult
from .distribuiti_carico import CaricoDistribuitoResult
from .distribuiti_verifiche import VerificheDistribuitoResult
from .giunti import GiuntiResult
from .materiali import MaterialiResult
from .models import PavimentoIndustrialeInput
from .output import PavimentoIndustrialeOutput
from .relazione_concentrati import (
    traccia_geometria_e_resistenze,
    traccia_tensioni_westergaard,
    traccia_verifiche_concentrati,
)
from .relazione_distribuiti import traccia_carico_distribuito, traccia_verifiche_distribuito
from .relazione_giunti import traccia_giunti
from .relazione_materiali_sottofondo import traccia_materiali_sottofondo
from .sottofondo import SottofondoResult


def relazione(inputs: PavimentoIndustrialeInput, output: PavimentoIndustrialeOutput) -> tuple[Traccia, ...]:
    mat: MaterialiResult = output.materiali
    sott: SottofondoResult = output.sottofondo
    arm: ArmaturaResult = output.armatura
    carico: CaricoDistribuitoResult = output.distribuiti.carico
    verifiche: VerificheDistribuitoResult = output.distribuiti.verifiche
    concentrati: ConcentratiResult = output.concentrati
    giunti: GiuntiResult = output.giunti
    return (
        traccia_materiali_sottofondo(inputs, mat, sott, arm),
        traccia_carico_distribuito(inputs, carico),
        traccia_verifiche_distribuito(mat, sott, carico, verifiche, arm),
        traccia_geometria_e_resistenze(inputs, mat, sott, concentrati),
        traccia_tensioni_westergaard(inputs, sott, concentrati),
        traccia_verifiche_concentrati(inputs, mat, sott, arm, concentrati),
        traccia_giunti(inputs, giunti),
    )
