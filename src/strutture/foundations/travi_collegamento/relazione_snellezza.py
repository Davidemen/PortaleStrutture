"""Verified restatement (docs/architecture-phase2.md) of `snellezza_ntc.py` (NTC2018 §7.2.5,
`λlim = 25/sqrt(NEd/(Ac·fcd))`) and `snellezza_en.py` (EN1992-1-1 §5.8.3.1 eq. 5.13N,
`λlim = 20·A·B·C/sqrt(n)`). `raggio_inerzia_debole_mm`'s own `min`/`max` selection of the weak axis
is restated with the notation grammar's own `min`/`max` functions (`geometria.
raggio_inerzia_debole_mm` docstring). `NEd` is converted kN->N by VALUE (not a bare literal inside
the formula, docs/architecture-phase2.md §6 lesson 5): the sqrt denominator mixes `Ac`[mm²]·`fcd`
[MPa] (=N) with `NEd`, so a uniform `scala` on the whole result cannot express it."""
from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.units import N_PER_KN

from .azione import AzioneResult
from .materiali import MaterialiResult
from .models import TraviCollegamentoInput
from .snellezza_en import LAMBDA_LIM_A_ASSUNTO, LAMBDA_LIM_BASE_EC2, LAMBDA_LIM_C_ASSUNTO, SnellezzaEnResult
from .snellezza_ntc import LAMBDA_LIM_COEFFICIENTE_NTC, SnellezzaNtcResult

FORMULA_L0 = "β * l"
FORMULA_I = "sqrt(min(B, H)^3 * max(B, H) / 12 / (B * H))"


def traccia_snellezza_ntc(inputs: TraviCollegamentoInput, mat: MaterialiResult, az: AzioneResult, snel: SnellezzaNtcResult) -> Traccia:
    """4 passi: l0, i, λ, verifica λlim>λ (Check "Verifica snellezza")."""
    return Traccia(
        titolo="Controllo della snellezza (NTC2018)",
        passi=(_passo_l0(inputs, snel), _passo_i(inputs, snel), _passo_lambda(snel), _passo_verifica_ntc(mat, az, snel)),
    )


def _passo_l0(inputs: TraviCollegamentoInput, snel: SnellezzaNtcResult | SnellezzaEnResult) -> Passo:
    return Passo(
        simbolo="l_0", formula=FORMULA_L0,
        valori=(
            Valore(simbolo="β", valore=inputs.beta, descrizione="coefficiente per la luce di libera inflessione"),
            Valore(simbolo="l", valore=inputs.l_mm, unita="mm", descrizione="luce netta della trave di collegamento"),
        ),
        risultato=snel.l0_mm, unita="mm",
        nota="Lunghezza di libera inflessione.",
    )


def _passo_i(inputs: TraviCollegamentoInput, snel: SnellezzaNtcResult | SnellezzaEnResult) -> Passo:
    return Passo(
        simbolo="i", formula=FORMULA_I,
        valori=(
            Valore(simbolo="B", valore=inputs.b_mm, unita="mm", descrizione="base della sezione"),
            Valore(simbolo="H", valore=inputs.h_mm, unita="mm", descrizione="altezza della sezione"),
        ),
        risultato=snel.i_mm, unita="mm",
        nota="Raggio d'inerzia attorno all'asse debole della sezione rettangolare.",
    )


def _passo_lambda(snel: SnellezzaNtcResult | SnellezzaEnResult) -> Passo:
    return Passo(
        simbolo="λ", formula="l_0 / i",
        valori=(
            Valore(simbolo="l_0", valore=snel.l0_mm, unita="mm", descrizione="calcolato sopra"),
            Valore(simbolo="i", valore=snel.i_mm, unita="mm", descrizione="calcolato sopra"),
        ),
        risultato=snel.lambda_, unita="-",
        nota="Snellezza della trave di collegamento.",
    )


def _passo_verifica_ntc(mat: MaterialiResult, az: AzioneResult, snel: SnellezzaNtcResult) -> Passo:
    soddisfatta = snel.verifica.passed
    return Passo(
        simbolo="λ_lim", formula=f"{LAMBDA_LIM_COEFFICIENTE_NTC:g} / sqrt(N_Ed / (A_c * f_cd)) > λ",
        valori=(
            Valore(simbolo="N_Ed", valore=az.ned_kN * N_PER_KN, unita="N", descrizione="forza assiale di progetto, convertita da kN a N, calcolata sopra"),
            Valore(simbolo="A_c", valore=mat.ac_mm2, unita="mm2", descrizione="area della sezione di calcestruzzo, calcolata sopra"),
            Valore(simbolo="f_cd", valore=mat.fcd_MPa, unita="MPa", descrizione="tensione di calcolo a compressione del calcestruzzo, calcolata sopra"),
            Valore(simbolo="λ", valore=snel.lambda_, descrizione="snellezza, calcolata sopra"),
        ),
        risultato=snel.lambda_lim, unita="-", clausola=snel.verifica.clause,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota=f"Snellezza limite (coefficiente empirico {LAMBDA_LIM_COEFFICIENTE_NTC:g}, NTC2018 §7.2.5).",
    )


def traccia_snellezza_en(inputs: TraviCollegamentoInput, mat: MaterialiResult, az: AzioneResult, snel: SnellezzaEnResult) -> Traccia:
    """5 passi: l0, i, ω, λ, verifica λlim>λ (Check "Verifica snellezza")."""
    return Traccia(
        titolo="Controllo della snellezza (EN1998)",
        passi=(_passo_l0(inputs, snel), _passo_i(inputs, snel), _passo_omega(mat, snel), _passo_lambda(snel), _passo_verifica_en(mat, az, snel)),
    )


def _passo_omega(mat: MaterialiResult, snel: SnellezzaEnResult) -> Passo:
    return Passo(
        simbolo="ω", formula="A_s * f_yd / (A_c * f_cd)",
        valori=(
            Valore(simbolo="A_s", valore=mat.as_mm2, unita="mm2", descrizione="area delle barre longitudinali, calcolata sopra"),
            Valore(simbolo="f_yd", valore=mat.fyd_MPa, unita="MPa", descrizione="tensione di calcolo di snervamento dell'acciaio, calcolata sopra"),
            Valore(simbolo="A_c", valore=mat.ac_mm2, unita="mm2", descrizione="area della sezione di calcestruzzo, calcolata sopra"),
            Valore(simbolo="f_cd", valore=mat.fcd_MPa, unita="MPa", descrizione="tensione di calcolo a compressione del calcestruzzo, calcolata sopra"),
        ),
        risultato=snel.omega, unita="-",
        nota="Rapporto meccanico di armatura.",
    )


def _passo_verifica_en(mat: MaterialiResult, az: AzioneResult, snel: SnellezzaEnResult) -> Passo:
    soddisfatta = snel.verifica.passed
    formula = (
        f"{LAMBDA_LIM_BASE_EC2:g} * {LAMBDA_LIM_A_ASSUNTO:g} * sqrt(1 + 2 * ω) * {LAMBDA_LIM_C_ASSUNTO:g} "
        "/ sqrt(N_Ed / (A_c * f_cd)) > λ"
    )
    return Passo(
        simbolo="λ_lim", formula=formula,
        valori=(
            Valore(simbolo="ω", valore=snel.omega, descrizione="calcolato sopra"),
            Valore(simbolo="N_Ed", valore=az.ned_kN * N_PER_KN, unita="N", descrizione="forza assiale di progetto, convertita da kN a N, calcolata sopra"),
            Valore(simbolo="A_c", valore=mat.ac_mm2, unita="mm2", descrizione="area della sezione di calcestruzzo, calcolata sopra"),
            Valore(simbolo="f_cd", valore=mat.fcd_MPa, unita="MPa", descrizione="tensione di calcolo a compressione del calcestruzzo, calcolata sopra"),
            Valore(simbolo="λ", valore=snel.lambda_, descrizione="snellezza, calcolata sopra"),
        ),
        risultato=snel.lambda_lim, unita="-", clausola=snel.verifica.clause,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota=f"Snellezza limite (formula a curva di stabilità EC2, A={LAMBDA_LIM_A_ASSUNTO:g} e "
             f"C={LAMBDA_LIM_C_ASSUNTO:g} assunti — φef e rm non sono dati d'ingresso del foglio).",
    )
