"""Shared helpers for the `muro-sostegno` relazione modules (docs/architecture-phase2.md §6): the
calculation code is never touched — every helper here only reads fields `run_muro_sostegno` (or
one of the package's own step functions) already computed, and picks the combinazione each
`Traccia` uses as its worked example.

Many-rows rule (docs/architecture-phase2.md §5): with 8 combinazioni per verification group, only
the GOVERNING one gets the full symbolic derivation (thrust, weights, moments); the Traccia title
always names it. `combo_governante_stabilita` answers "which one" for ribaltamento/scorrimento/
pressioni (the three share the same thrust/weights physics, NTC2018 §6.5.3.1.1/§6.5.3.1.2): the
combinazione with the smallest safety margin of either check, i.e. the one an engineer would reach
for first. The three reinforcement groups and the optional bearing-capacity check already carry
their OWN governing combinazione on the output (`combo_governante`), read directly instead.
"""
import math

from .models import (
    MuroSostegnoOutput,
    NomeCombo,
    PressioniCombo,
    RibaltamentoScorrimentoCombo,
    SpintaCombo,
)

PI_GRECO = math.pi


def trova_spinta(output: MuroSostegnoOutput, nome: NomeCombo) -> SpintaCombo:
    return next(c for c in output.spinte if c.nome == nome)


def trova_verifica(output: MuroSostegnoOutput, nome: NomeCombo) -> RibaltamentoScorrimentoCombo:
    return next(c for c in output.ribaltamento_scorrimento if c.nome == nome)


def trova_pressioni(output: MuroSostegnoOutput, nome: NomeCombo) -> PressioniCombo:
    return next(c for c in output.pressioni_terreno if c.nome == nome)


def combo_governante_stabilita(output: MuroSostegnoOutput) -> NomeCombo:
    """La combinazione con il minor margine di sicurezza fra ribaltamento e scorrimento, usata
    come esempio svolto per la spinta, i pesi stabilizzanti, il ribaltamento/scorrimento e le
    pressioni sul terreno."""
    return min(output.ribaltamento_scorrimento, key=lambda c: min(c.or_ribaltamento, c.os_scorrimento)).nome


def nome_combo_leggibile(nome: NomeCombo) -> str:
    """Le combinazioni sismiche differiscono solo nel segno di kv: richiamarlo esplicitamente
    (stessa scelta di `tool.py::_nome_combo_leggibile`, non importata per non introdurre un
    accoppiamento fra la relazione e la registrazione del Tool)."""
    if nome == "SISMA_1":
        return f"{nome} (+kv)"
    if nome == "SISMA_2":
        return f"{nome} (−kv)"
    return nome
