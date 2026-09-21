"""Verified restatement (docs/architecture-phase2.md) of the geometry steps used pervasively by
every later `Traccia` of this package: altezza utile `d`, armatura tesa presente `A_s` and
armatura a taglio presente `A_sw`. The calculation code (`geometria.py`, `armatura_limiti.py`) is
never touched; the bar-count/diameter formulas below mirror `armatura_limiti._area_ferri_tesi`/
`_area_staffe_per_m` exactly (`shared.rebar_catalog.bars_area`/`asw_per_m`, A = π/4·⌀²).

Notation identifiers must be grammar-legal (`shared.relazione.notazione`): the UI symbol hints
"⌀_1"/"⌀_2"/"⌀_sw,1"/"⌀_sw,2" are not (a diameter sign is not a letter), so bar/stirrup diameters
use "φ" here instead, with a `descrizione` naming the original field; bar/leg counts have no UI
symbol at all, so "n_1"/"n_2"/"n_br,1"/"n_br,2" are introduced the same way.
"""
import math

from strutture.shared.relazione import Passo, Traccia, Valore

from .geometria import LEVA_INTERNA_FATTORE
from .models import TraveRettangolareInput, TraveRettangolareOutput

PI_GRECO = math.pi
MM2_PER_M_PER_MM = 1000.0  # asw_per_m: area per metro -> per mm di passo (shared.units.MM_PER_M)


def traccia_geometria(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Traccia:
    """4 passi: altezza utile, braccio di leva interno, armatura tesa presente, armatura a taglio
    presente."""
    return Traccia(
        titolo="Geometria della sezione",
        passi=(_passo_d(inputs, output), _passo_z(output), _passo_as(inputs, output), _passo_asw(inputs, output)),
    )


def _passo_d(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    return Passo(
        simbolo="d",
        formula="h - c",
        valori=(
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="altezza della sezione"),
            Valore(simbolo="c", valore=inputs.copriferro_mm, unita="mm", descrizione="copriferro"),
        ),
        risultato=output.flessione.d_mm, unita="mm", clausola="NTC2018 §4.1.2.3.4.2",
        nota="Altezza utile della sezione, misurata all'asse delle barre tese.",
    )


def _passo_z(output: TraveRettangolareOutput) -> Passo:
    """Review finding (MISSING_STEP): z=0,9·d entrava in V_Rcd/V_Rsd (`relazione_taglio.py`) senza
    che alcun passo lo derivasse."""
    return Passo(
        simbolo="z", formula=f"{LEVA_INTERNA_FATTORE:g} * d",
        valori=(Valore(simbolo="d", valore=output.flessione.d_mm, unita="mm"),),
        risultato=output.armatura.z_mm, unita="mm", clausola="EN 1992-1-1 §6.2.3",
        nota="Braccio di leva interno (approssimazione usuale z ≈ 0,9·d), usato dalla resistenza a taglio.",
    )


def _passo_as(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    valori = [
        Valore(simbolo="n_1", valore=float(inputs.n_ferri1), descrizione="numero di ferri tesi, primo strato"),
        Valore(simbolo="π", valore=PI_GRECO),
        Valore(simbolo="φ_1", valore=inputs.diametro_ferri1_mm, unita="mm", descrizione="diametro dei ferri tesi, primo strato (⌀_1 in input)"),
    ]
    formula = "n_1 * π * φ_1^2 / 4"
    if inputs.n_ferri2 > 0:
        formula = f"{formula} + n_2 * π * φ_2^2 / 4"
        valori += [
            Valore(simbolo="n_2", valore=float(inputs.n_ferri2), descrizione="numero di ferri tesi, secondo strato"),
            Valore(simbolo="φ_2", valore=inputs.diametro_ferri2_mm, unita="mm", descrizione="diametro dei ferri tesi, secondo strato (⌀_2 in input)"),
        ]
    return Passo(
        simbolo="A_s", formula=formula, valori=tuple(valori),
        risultato=output.armatura.as_o_mm2, unita="mm²", clausola="NTC2018 §4.1.6.1.1",
        nota="Area di armatura tesa effettivamente presente (As,o).",
    )


def _passo_asw(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    valori = [
        Valore(simbolo="n_br,1", valore=float(inputs.n_bracci_staffe1), descrizione="numero di bracci delle staffe, primo tratto"),
        Valore(simbolo="π", valore=PI_GRECO),
        Valore(simbolo="φ_sw,1", valore=inputs.diametro_staffe1_mm, unita="mm", descrizione="diametro delle staffe, primo tratto (⌀_sw,1 in input)"),
        Valore(simbolo="s_1", valore=inputs.passo_staffe1_mm, unita="mm", descrizione="passo delle staffe, primo tratto"),
    ]
    formula = f"n_br,1 * π * φ_sw,1^2 / 4 * {MM2_PER_M_PER_MM:g} / s_1"
    if inputs.n_bracci_staffe2 > 0:
        formula = f"{formula} + n_br,2 * π * φ_sw,2^2 / 4 * {MM2_PER_M_PER_MM:g} / s_1"
        valori += [
            Valore(simbolo="n_br,2", valore=float(inputs.n_bracci_staffe2), descrizione="numero di bracci delle staffe, secondo tratto"),
            Valore(simbolo="φ_sw,2", valore=inputs.diametro_staffe2_mm, unita="mm", descrizione="diametro delle staffe, secondo tratto (⌀_sw,2 in input)"),
        ]
    return Passo(
        simbolo="A_sw", formula=formula, valori=tuple(valori),
        risultato=output.armatura.asw_per_m_mm2, unita="mm²/m", clausola="NTC2018 §4.1.6.1.1",
        nota="Area di staffe per metro effettivamente presente; entrambi i tratti condividono il passo s_1.",
    )
