"""Verified restatement of the `fond-trave-collegamento` formulas for "Sviluppo dei calcoli"
(docs/architecture-phase2.md §6, wave-2/3 adoption). Pure function of the tool's own validated
inputs and already-computed output; the calculation code of this package is never touched — see
each `relazione_*.py` module's own docstring for which package module it restates. `norma`
switches the whole trace between the NTC2018 branch (4 Check: compressione, trazione, snellezza,
staffe) and the EN1998 branch (7 Check: compressione, trazione, snellezza, armatura minima,
geometria minima ×2, staffe minime) — mirroring `tool.py::run`'s own dispatch. Standard mode only
(`execute(..., con_relazione=True)` never calls it with `legacy_compat=True`)."""
from strutture.shared.relazione import Traccia

from .models import TraviCollegamentoInput
from .output import TraviCollegamentoOutput
from .relazione_azione_materiali import traccia_azione, traccia_materiali
from .relazione_minimi_en import traccia_armatura_minima_en, traccia_geometria_minima_en, traccia_staffe_minime_en
from .relazione_minimi_ntc import traccia_minimi_ntc
from .relazione_sismica import traccia_sismica_en, traccia_sismica_ntc
from .relazione_snellezza import traccia_snellezza_en, traccia_snellezza_ntc
from .relazione_verifiche_sezione import traccia_compressione, traccia_trazione

CLAUSOLA_SEZIONE_NTC = "NTC2018 §7.2.5"
CLAUSOLA_SEZIONE_EN = "EN1998-5 §5.4.1.2"


def relazione(inputs: TraviCollegamentoInput, output: TraviCollegamentoOutput) -> tuple[Traccia, ...]:
    if inputs.norma == "NTC2018":
        return _relazione_ntc(inputs, output)
    return _relazione_en(inputs, output)


def _relazione_ntc(inputs: TraviCollegamentoInput, output: TraviCollegamentoOutput) -> tuple[Traccia, ...]:
    assert output.sismica_ntc is not None and output.snellezza_ntc is not None and output.minimi_ntc is not None
    return (
        traccia_sismica_ntc(inputs, output.sismica_ntc),
        traccia_materiali(inputs, output.materiali),
        traccia_azione(inputs, output.sismica_ntc, output.azione),
        traccia_compressione(output.materiali, output.azione, output.compressione, CLAUSOLA_SEZIONE_NTC),
        traccia_trazione(output.materiali, output.azione, output.trazione, CLAUSOLA_SEZIONE_NTC),
        traccia_snellezza_ntc(inputs, output.materiali, output.azione, output.snellezza_ntc),
        traccia_minimi_ntc(inputs, output.materiali, output.minimi_ntc),
    )


def _relazione_en(inputs: TraviCollegamentoInput, output: TraviCollegamentoOutput) -> tuple[Traccia, ...]:
    assert (
        output.sismica_en is not None and output.snellezza_en is not None and output.minimi_en is not None
    )
    minimi = output.minimi_en
    return (
        traccia_sismica_en(inputs, output.sismica_en),
        traccia_materiali(inputs, output.materiali),
        traccia_azione(inputs, output.sismica_en, output.azione),
        traccia_compressione(output.materiali, output.azione, output.compressione, CLAUSOLA_SEZIONE_EN),
        traccia_trazione(output.materiali, output.azione, output.trazione, CLAUSOLA_SEZIONE_EN),
        traccia_snellezza_en(inputs, output.materiali, output.azione, output.snellezza_en),
        traccia_armatura_minima_en(output.materiali, minimi.armatura_longitudinale),
        traccia_geometria_minima_en(inputs, minimi.geometria),
        traccia_staffe_minime_en(inputs, output.materiali, minimi.staffe),
    )
