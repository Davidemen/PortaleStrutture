"""Verified restatement (docs/architecture-phase2.md) of `distribuiti_carico.py`/`distribuiti_
momenti.py`/`distribuiti_verifiche.py` (Westergaard infinite-plate-on-Winkler UDL moments +
stress/crack/reinforcement checks). Standard mode only (this module is never called with
`legacy_compat=True`): the top-fibre ULS stress check uses `fcfd` for both fibres, not the sheet's
`fcfk` (sup) / `fcfd` (inf) mismatch — `distribuiti_verifiche.py`'s own docstring, review-equivalent
fix already in the calculation code, restated as-is here.

The moment formulas (`M = coefficiente·q/λ²/1000`) are embedded directly inside each check's own
formula (not given a separate `Passo`): each moment is used by exactly one check here, so a
dedicated step would only repeat the same sub-expression the check already shows."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .armatura import ArmaturaResult
from .distribuiti_carico import CaricoDistribuitoResult
from .distribuiti_momenti import WESTERGAARD_UDL_COEFFICIENT_INF, WESTERGAARD_UDL_COEFFICIENT_SUP
from .distribuiti_verifiche import VerificheDistribuitoResult
from .materiali import FCTM_RCK_COEFFICIENT, MaterialiResult
from .models import PavimentoIndustrialeInput
from .sottofondo import SottofondoResult
from .tables import CRACK_DERATING_FACTOR, DAN_PER_KN_M2

CLAUSOLA = "CNR-DT211/2014"


def traccia_carico_distribuito(inputs: PavimentoIndustrialeInput, carico: CaricoDistribuitoResult) -> Traccia:
    """2 passi: q_SLU, q_SLE,f."""
    return Traccia(titolo="Carico distribuito: combinazioni", passi=(_passo_q_slu(inputs, carico), _passo_q_sle(inputs, carico)))


def _passo_q_slu(inputs: PavimentoIndustrialeInput, carico: CaricoDistribuitoResult) -> Passo:
    return Passo(
        simbolo="q_SLU", formula=f"(G / {DAN_PER_KN_M2:g}) * γ_G + (Q / {DAN_PER_KN_M2:g}) * γ_Q",
        valori=(
            Valore(simbolo="G", valore=inputs.g_daN_m2, unita="daN/m2", descrizione="carico permanente distribuito"),
            Valore(simbolo="γ_G", valore=inputs.gamma_g, descrizione="coefficiente parziale permanente"),
            Valore(simbolo="Q", valore=inputs.q_daN_m2, unita="daN/m2", descrizione="carico variabile distribuito"),
            Valore(simbolo="γ_Q", valore=inputs.gamma_q, descrizione="coefficiente parziale variabile"),
        ),
        risultato=carico.q_slu_kN_m2, unita="kN/m2",
        nota="Carico combinato allo SLU.",
    )


def _passo_q_sle(inputs: PavimentoIndustrialeInput, carico: CaricoDistribuitoResult) -> Passo:
    return Passo(
        simbolo="q_SLE,f", formula=f"(G / {DAN_PER_KN_M2:g}) + (Q / {DAN_PER_KN_M2:g}) * ψ_1",
        valori=(
            Valore(simbolo="G", valore=inputs.g_daN_m2, unita="daN/m2", descrizione="carico permanente distribuito"),
            Valore(simbolo="Q", valore=inputs.q_daN_m2, unita="daN/m2", descrizione="carico variabile distribuito"),
            Valore(simbolo="ψ_1", valore=inputs.psi1_distribuito, descrizione="coefficiente di combinazione frequente"),
        ),
        risultato=carico.q_sle_freq_kN_m2, unita="kN/m2",
        nota="Carico combinato SLE, combinazione frequente.",
    )


def _formula_momento(coefficiente: float, simbolo_q: str) -> str:
    return f"{coefficiente:g} * {simbolo_q} / λ^2 / 1000"


def traccia_verifiche_distribuito(
    mat: MaterialiResult, sott: SottofondoResult, carico: CaricoDistribuitoResult,
    verifiche: VerificheDistribuitoResult, arm: ArmaturaResult,
) -> Traccia:
    """6 passi, uno per ciascuno dei 6 Check di `distribuiti_verifiche.py`."""
    return Traccia(
        titolo="Verifiche del carico distribuito",
        passi=(
            _passo_tensionale(mat, sott, carico, verifiche, sup=True),
            _passo_tensionale(mat, sott, carico, verifiche, sup=False),
            _passo_fessurazione(mat, sott, carico, verifiche, sup=True),
            _passo_fessurazione(mat, sott, carico, verifiche, sup=False),
            _passo_armatura(mat, sott, carico, verifiche, arm, sup=True),
            _passo_armatura(mat, sott, carico, verifiche, arm, sup=False),
        ),
    )


def _valori_comuni(sott: SottofondoResult, carico: CaricoDistribuitoResult, *, sle: bool) -> tuple[Valore, ...]:
    q = carico.q_sle_freq_kN_m2 if sle else carico.q_slu_kN_m2
    simbolo_q = "q_SLE,f" if sle else "q_SLU"
    return (
        Valore(simbolo=simbolo_q, valore=q, unita="kN/m2", descrizione="calcolato sopra"),
        Valore(simbolo="λ", valore=sott.lambda_mm1, unita="1/mm", descrizione="parametro di rigidezza della piastra, calcolato sopra"),
    )


def _passo_tensionale(
    mat: MaterialiResult, sott: SottofondoResult, carico: CaricoDistribuitoResult, verifiche: VerificheDistribuitoResult, *, sup: bool,
) -> Passo:
    coeff = WESTERGAARD_UDL_COEFFICIENT_SUP if sup else WESTERGAARD_UDL_COEFFICIENT_INF
    fibra = "sup" if sup else "inf"
    sigma = verifiche.sigma_c_max_sup_MPa if sup else verifiche.sigma_c_max_inf_MPa
    check = verifiche.verifica_tensionale_sup if sup else verifiche.verifica_tensionale_inf
    formula = f"({_formula_momento(coeff, 'q_SLU')}) / W * 1000 <= f_cfd"
    return Passo(
        simbolo=f"σ_c,max,{fibra}", formula=formula,
        valori=(
            *_valori_comuni(sott, carico, sle=False),
            Valore(simbolo="W", valore=sott.w_mm3_m, unita="mm3/m", descrizione="modulo di resistenza a flessione, calcolato sopra"),
            Valore(simbolo="f_cfd", valore=mat.fcfd_MPa, unita="MPa", descrizione="resistenza di calcolo a trazione per flessione, calcolata sopra"),
        ),
        risultato=sigma, unita="MPa", clausola=check.clause,
        esito="soddisfatta" if check.passed else "non soddisfatta",
        nota=f"Tensione di flessione ULS, fibra {fibra} (Westergaard, piastra infinita su suolo alla Winkler, carico uniformemente distribuito).",
    )


def _passo_fessurazione(
    mat: MaterialiResult, sott: SottofondoResult, carico: CaricoDistribuitoResult, verifiche: VerificheDistribuitoResult, *, sup: bool,
) -> Passo:
    coeff = WESTERGAARD_UDL_COEFFICIENT_SUP if sup else WESTERGAARD_UDL_COEFFICIENT_INF
    fibra = "sup" if sup else "inf"
    sigma = verifiche.sigma_c_t_sup_MPa if sup else verifiche.sigma_c_t_inf_MPa
    check = verifiche.verifica_fessurazione_sup if sup else verifiche.verifica_fessurazione_inf
    # `(2 / 3)` written as a literal sub-expression, not `FCTM_EXPONENT`'s rounded `:g` text — see
    # `relazione_materiali_sottofondo._passo_fcfd`'s comment (same exact-value/legible-render reason).
    formula = f"({_formula_momento(coeff, 'q_SLE,f')}) / W * 1000 <= ({FCTM_RCK_COEFFICIENT:g} * R_ck^(2 / 3)) / {CRACK_DERATING_FACTOR:g}"
    return Passo(
        simbolo=f"σ_c,t,{fibra}", formula=formula,
        valori=(
            *_valori_comuni(sott, carico, sle=True),
            Valore(simbolo="W", valore=sott.w_mm3_m, unita="mm3/m", descrizione="modulo di resistenza a flessione, calcolato sopra"),
            Valore(simbolo="R_ck", valore=mat.rck_MPa, unita="MPa", descrizione="resistenza cubica caratteristica, valore tabellare"),
        ),
        risultato=sigma, unita="MPa", clausola=check.clause,
        esito="soddisfatta" if check.passed else "non soddisfatta",
        nota=f"Tensione di trazione SLE frequente, fibra {fibra}; limite fctm/{CRACK_DERATING_FACTOR:g} (fattore di derating non da una clausola verificata, vedi tables.py).",
    )


def _passo_armatura(
    mat: MaterialiResult, sott: SottofondoResult, carico: CaricoDistribuitoResult, verifiche: VerificheDistribuitoResult,
    arm: ArmaturaResult, *, sup: bool,
) -> Passo:
    coeff = WESTERGAARD_UDL_COEFFICIENT_SUP if sup else WESTERGAARD_UDL_COEFFICIENT_INF
    fibra = "sup" if sup else "inf"
    check = verifiche.verifica_armatura_sup if sup else verifiche.verifica_armatura_inf
    m_nmm_m = coeff * carico.q_slu_kN_m2 / sott.lambda_mm1**2 / 1000.0
    formula = f"({_formula_momento(coeff, 'q_SLU')}) / M_Rd <= 1"
    return Passo(
        simbolo=f"M_SLU,{fibra}/M_Rd", formula=formula,
        valori=(
            *_valori_comuni(sott, carico, sle=False),
            Valore(simbolo="M_Rd", valore=arm.mrd_Nmm_m, unita="N·m/m", descrizione="momento resistente della sezione armata, calcolato sopra (N·m/m, non Nmm/m: v. relazione_materiali_sottofondo.py)"),
        ),
        risultato=m_nmm_m / arm.mrd_Nmm_m, unita="-", clausola=check.clause,
        esito="soddisfatta" if check.passed else "non soddisfatta",
        nota=f"Tasso di lavoro dell'armatura, fibra {fibra}.",
    )
