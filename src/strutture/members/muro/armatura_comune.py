"""Helpers shared by the three reinforcement groups (paramento, fondazione valle, fondazione
monte) — split out of `tool.py`, regola dura 12 dei moduli piccoli.
"""
from strutture.shared.materials.concrete import concrete_properties
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.report import Check

from . import armatura_minima
from .models import MuroSostegnoInput


def armatura_minima_cm2_m(inputs: MuroSostegnoInput, d_m: float) -> float:
    return armatura_minima.as_min_cm2_m(
        fctm_MPa=concrete_properties(inputs.tipo_cls).fctm_MPa,
        fyk_MPa=rebar_properties(inputs.grado_acciaio).fyk_MPa, d_m=d_m,
    )


def check_armatura_minima(nome: str, risultato: object) -> Check:
    disposta = armatura_minima.area_disposta_cm2_m(diametro_mm=risultato.diametro_mm, passo_m=risultato.passo_m)
    return Check(
        name=nome, passed=disposta + 1e-9 >= risultato.as_min_cm2_m, clause="NTC2018 §4.1.6.1.1",
        detail=f"{disposta:.2f} >= {risultato.as_min_cm2_m:.2f} cm²/m",  # short: the detail column is ~150 px wide
        value=disposta, limit=risultato.as_min_cm2_m, unit="cm2/m",
    )
