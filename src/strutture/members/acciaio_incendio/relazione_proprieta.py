"""Verified restatement (docs/architecture-phase2.md) of `proprieta.py` (`acciaio-proprieta-
temperatura` — EN1993-1-2 §3.2.1 Tab. 3.1). k_y,θ/k_p,θ/k_E,θ are a piecewise-linear interpolation
of Tab. 3.1 (`strutture.shared.fire_reduction.reduction_factors`, `strutture.shared.tables.
interp_lookup`) — no formula an engineer would write, so each is restated as a `Passo` whose
`formula` is the identifier itself and whose `nota` names the table
(docs/architecture-phase2.md §6's "lookup only" fallback). This tool has no `Check` (`proprieta_tool.
run` calls `success(data, inputs)` with no `checks=`): the trace is a SHORT one, entirely
informative, restating the 3 highlighted outputs (f_p,θ, f_y,θ, E_a,θ).
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .proprieta_models import ProprietaTemperaturaInput, ProprietaTemperaturaOutput

_TABELLA = "EN1993-1-2 Tab. 3.1 (interpolazione lineare fra i nodi a 100°C)"


def relazione_proprieta(inputs: ProprietaTemperaturaInput, output: ProprietaTemperaturaOutput) -> tuple[Traccia, ...]:
    """6 passi: k_y,θ, k_p,θ, k_E,θ (lookup Tab. 3.1), f_y,θ, f_p,θ, E_a,θ (evidenziati)."""
    return (
        Traccia(
            titolo="Riduzione delle proprietà meccaniche dell'acciaio a temperatura θ",
            passi=(
                _passo_fattore(inputs, "k_y,θ", output.ky_theta),
                _passo_fattore(inputs, "k_p,θ", output.kp_theta),
                _passo_fattore(inputs, "k_E,θ", output.kE_theta),
                _passo_derivato(inputs, "f_y,θ", "f_yk", inputs.fyk_MPa, "k_y,θ", output.ky_theta, output.fy_theta_MPa, "tensione di snervamento efficace (classi 1-2)"),
                _passo_derivato(inputs, "f_p,θ", "f_yk", inputs.fyk_MPa, "k_p,θ", output.kp_theta, output.fp_theta_MPa, "limite di proporzionalità (classi 3-4)"),
                _passo_derivato(inputs, "E_a,θ", "E_a", inputs.ea_20_MPa, "k_E,θ", output.kE_theta, output.ea_theta_MPa, "modulo elastico"),
            ),
        ),
    )


def _passo_fattore(inputs: ProprietaTemperaturaInput, simbolo: str, valore: float) -> Passo:
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=valore, descrizione=f"lettura tabellare a θ={inputs.theta_C:g}°C"),),
        risultato=valore, unita="-", clausola=_TABELLA,
    )


def _passo_derivato(
    inputs: ProprietaTemperaturaInput, simbolo: str, simbolo_base: str, valore_base: float,
    simbolo_fattore: str, valore_fattore: float, risultato: float, descrizione: str,
) -> Passo:
    return Passo(
        simbolo=simbolo, formula=f"{simbolo_base} * {simbolo_fattore}",
        valori=(
            Valore(simbolo=simbolo_base, valore=valore_base, unita="MPa"),
            Valore(simbolo=simbolo_fattore, valore=valore_fattore, descrizione="calcolato sopra"),
        ),
        risultato=risultato, unita="MPa", clausola="EN1993-1-2 §3.2.1",
        nota=f"{descrizione}, a θ={inputs.theta_C:g}°C.",
    )
