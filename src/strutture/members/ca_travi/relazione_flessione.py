"""Verified restatement (docs/architecture-phase2.md) of `flessione_slu.py` (Tool 2, NTC2018
§4.1.2.3.4.2, blocco di tensioni rettangolare) — profondità dell'asse neutro `y`, momento
resistente `M_Rd` (the header worked example of docs/architecture-phase2.md §0), compatibilità
delle deformazioni (`Check` "Duttilità sezione") and the flexural utilisation `Check` "Resistenza
a flessione" (`M_Ed/M_Rd`, a highlighted output). Standard mode only (this module is never called
with `legacy_compat=True`): `STRESS_BLOCK_FATTORE` (0.8, not the legacy 0.81) applies throughout.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .flessione_slu import EPS_CU_PERMILLE, STRESS_BLOCK_FATTORE
from .models import TraveRettangolareInput, TraveRettangolareOutput

FATTORE_BRACCIO_MRD = STRESS_BLOCK_FATTORE / 2.0  # M_Rd = As*fyd*(d - fattore_braccio*y)


def traccia_flessione(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Traccia:
    """4 passi: asse neutro, M_Rd, duttilità (Check), utilizzazione a flessione (Check)."""
    return Traccia(
        titolo="Resistenza a flessione",
        passi=(
            _passo_y(inputs, output), _passo_mrd(output), _passo_duttilita(output),
            _passo_utilizzazione(inputs, output),
        ),
    )


def _passo_y(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    armatura, materiali, flessione = output.armatura, output.materiali, output.flessione
    return Passo(
        simbolo="y",
        formula=f"A_s * f_yd / (b * f_cd * {STRESS_BLOCK_FATTORE:g})",
        valori=(
            Valore(simbolo="A_s", valore=armatura.as_o_mm2, unita="mm²", descrizione="armatura tesa presente"),
            Valore(simbolo="f_yd", valore=materiali.acciaio.fyd_MPa, unita="MPa", descrizione="tensione di calcolo di snervamento dell'acciaio"),
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm", descrizione="base della trave"),
            Valore(simbolo="f_cd", valore=materiali.calcestruzzo.fcd_MPa, unita="MPa", descrizione="resistenza di calcolo a compressione del calcestruzzo"),
        ),
        risultato=flessione.y_mm, unita="mm", clausola="NTC2018 §4.1.2.3.4.2",
        nota="Profondità dell'asse neutro nel blocco di tensioni rettangolare.",
    )


def _passo_mrd(output: TraveRettangolareOutput) -> Passo:
    armatura, materiali, flessione = output.armatura, output.materiali, output.flessione
    return Passo(
        simbolo="M_Rd",
        formula=f"A_s * f_yd * (d - {FATTORE_BRACCIO_MRD:g} * y)",
        valori=(
            Valore(simbolo="A_s", valore=armatura.as_o_mm2, unita="mm²"),
            Valore(simbolo="f_yd", valore=materiali.acciaio.fyd_MPa, unita="MPa"),
            Valore(simbolo="d", valore=flessione.d_mm, unita="mm", descrizione="altezza utile"),
            Valore(simbolo="y", valore=flessione.y_mm, unita="mm", descrizione="profondità dell'asse neutro"),
        ),
        risultato=flessione.mrd_kNm, unita="kNm", scala=1e-6, clausola="NTC2018 §4.1.2.3.4.2",
        nota="Momento resistente a flessione, semplice armatura.",
    )


def _passo_duttilita(output: TraveRettangolareOutput) -> Passo:
    materiali, flessione = output.materiali, output.flessione
    return Passo(
        simbolo="ε_s",
        formula=f"{EPS_CU_PERMILLE:g} * (d - y) / y >= f_yd / E_s * 1000",
        valori=(
            Valore(simbolo="d", valore=flessione.d_mm, unita="mm"),
            Valore(simbolo="y", valore=flessione.y_mm, unita="mm"),
            Valore(simbolo="f_yd", valore=materiali.acciaio.fyd_MPa, unita="MPa"),
            Valore(simbolo="E_s", valore=materiali.acciaio.es_MPa, unita="MPa", descrizione="modulo elastico dell'acciaio"),
        ),
        risultato=flessione.eps_s_permille, unita="‰", clausola="NTC2018 §4.1.2.1.2.2",
        esito="soddisfatta" if flessione.acciaio_snervato else "non soddisfatta",
        nota="Compatibilità delle deformazioni: l'acciaio teso deve essere snervato (εs ≥ εyd) alla crisi della sezione.",
    )


def _passo_utilizzazione(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    flessione = output.flessione
    soddisfatta = flessione.tasso_sfruttamento <= 1.0
    return Passo(
        simbolo="M_Ed/M_Rd",
        formula="M_Ed / M_Rd <= 1",
        valori=(
            Valore(simbolo="M_Ed", valore=inputs.med_slu_kNm, unita="kNm", descrizione="momento flettente di calcolo allo SLU"),
            Valore(simbolo="M_Rd", valore=flessione.mrd_kNm, unita="kNm"),
        ),
        risultato=flessione.tasso_sfruttamento, unita="-", clausola="NTC2018 §4.1.2.3.4.2",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tasso di sfruttamento a flessione.",
    )
