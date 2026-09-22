"""Pydantic I/O models for the `muro-sostegno` tool (cantilever retaining wall, per metre run).

Inputs stay FLAT, ordered as in the sheet (rows 4-39). Outputs are nested per calculation group:
`geometria` (shared geometry/weights), `parametri_sismici` (Ss/ST/S), `spinte` (Tool 1 — active
thrust per combination), `ribaltamento_scorrimento` (Tool 2), `pressioni_terreno` (Tool 3).

This module stays the entry point for every public model (regola dura 15, i simboli non si
spostano dai punti d'ingresso già usati altrove): the models themselves live in the small sibling
modules below (regola dura 12, moduli di calcolo <= 150 righe) and are re-exported here.

Extension point for the reinforcement-design agent: append new nested result models in
`models_armatura.py` and new optional fields on `MuroSostegnoOutput` (`models_output.py`).
"""
from .models_armatura import (
    ArmaturaFondazioneMonteCombo,
    ArmaturaFondazioneMonteResult,
    ArmaturaFondazioneValleCombo,
    ArmaturaFondazioneValleResult,
    ArmaturaParamentoCombo,
    ArmaturaParamentoResult,
)
from .models_capacita_portante import CapacitaPortanteCombo, CapacitaPortanteFondazioneResult
from .models_common import NomeCombo
from .models_geometria import GeometriaResult, ParametriSismiciResult
from .models_input import MuroSostegnoInput
from .models_output import MuroSostegnoOutput
from .models_spinta import SpintaCombo
from .models_verifiche import PressioniCombo, RibaltamentoScorrimentoCombo

__all__ = [
    "ArmaturaFondazioneMonteCombo",
    "ArmaturaFondazioneMonteResult",
    "ArmaturaFondazioneValleCombo",
    "ArmaturaFondazioneValleResult",
    "ArmaturaParamentoCombo",
    "ArmaturaParamentoResult",
    "CapacitaPortanteCombo",
    "CapacitaPortanteFondazioneResult",
    "GeometriaResult",
    "MuroSostegnoInput",
    "MuroSostegnoOutput",
    "NomeCombo",
    "ParametriSismiciResult",
    "PressioniCombo",
    "RibaltamentoScorrimentoCombo",
    "SpintaCombo",
]
