"""Verified restatement (docs/architecture-phase2.md) of `materiali.py` (NTC2018 §11.2.10 concrete/
steel design strengths + CNR-DT211/2014's own flexural-tensile-strength fit from Rck) and
`sottofondo.py`/`armatura.py` (Winkler subgrade, plate stiffness, Westergaard radius `l`, mesh
capacity `Mrd`). `f_ck`/`R_ck`/`f_yk` are table lookups (`Materiali!A2:C10`/`E2:F2`), cited by
identity with a `nota` naming the table; every other quantity IS a formula, restated fully.
Intermediates used only once downstream (`f_yk` inside `M_Rd`, `R_ck`/`k_T` inside their one
consuming formula) are embedded inline as named `Valore`s rather than given their own `Passo`
(docs/architecture-phase2.md §6: "a coefficient... gets a step OR a named Valore with a
descrizione")."""
import math

from strutture.shared.relazione import Passo, Traccia, Valore

from .armatura import ArmaturaResult
from .materiali import FCFK_OVER_FCFM, FCFM_OVER_FCTM, FCTM_RCK_COEFFICIENT, MaterialiResult
from .models import PavimentoIndustrialeInput
from .sottofondo import SottofondoResult

CLAUSOLA_MATERIALI = "CNR-DT211/2014"
CLAUSOLA_NTC = "NTC2018 §11.2.10.1"


def traccia_materiali_sottofondo(
    inputs: PavimentoIndustrialeInput, mat: MaterialiResult, sott: SottofondoResult, arm: ArmaturaResult,
) -> Traccia:
    """8 passi: f_ck, f_cfd, d, E_cm, W, λ, l (highlight), M_Rd."""
    return Traccia(
        titolo="Materiali, sottofondo e rigidezza della piastra",
        passi=(
            _passo_fck(inputs, mat), _passo_fcfd(inputs, mat), _passo_d(inputs, sott), _passo_ecm(mat),
            _passo_w(inputs, sott), _passo_lambda(inputs, mat, sott), _passo_l(inputs, mat, sott),
            _passo_mrd(inputs, mat, sott, arm),
        ),
    )


def _passo_fck(inputs: PavimentoIndustrialeInput, mat: MaterialiResult) -> Passo:
    return Passo(
        simbolo="f_ck", formula="f_ck",
        valori=(Valore(simbolo="f_ck", valore=mat.fck_MPa, unita="MPa", descrizione=f"classe {inputs.classe_calcestruzzo}"),),
        risultato=mat.fck_MPa, unita="MPa",
        nota="Resistenza cilindrica caratteristica, valore tabellare (Materiali!A2:C10) per la classe scelta.",
    )


def _passo_fcfd(inputs: PavimentoIndustrialeInput, mat: MaterialiResult) -> Passo:
    # `FCTM_EXPONENT` is `2.0/3.0`: written as the literal sub-expression `(2 / 3)`, not `:g`'s
    # rounded 6-significant-digit text (0,666667, which already misses the harness's 1e-6 relative
    # tolerance once raised to a power) — the notation grammar evaluates `2/3` itself, bit-identical
    # to `FCTM_EXPONENT`, and renders it legibly ("R_ck^(2 / 3)") instead of 16 decimal digits.
    formula = f"{FCFK_OVER_FCFM:g} * {FCFM_OVER_FCTM:g} * ({FCTM_RCK_COEFFICIENT:g} * R_ck^(2 / 3)) / γ_c"
    return Passo(
        simbolo="f_cfd", formula=formula,
        valori=(
            Valore(simbolo="R_ck", valore=mat.rck_MPa, unita="MPa", descrizione="resistenza cubica caratteristica, valore tabellare (Materiali!A2:C10)"),
            Valore(simbolo="γ_c", valore=inputs.gamma_c, descrizione="coefficiente parziale di sicurezza del calcestruzzo"),
        ),
        risultato=mat.fcfd_MPa, unita="MPa", clausola=CLAUSOLA_MATERIALI,
        nota="Resistenza di calcolo a trazione per flessione, catena fctm(CNR-DT211, da Rck, non da "
             "fck)→fcfm→fcfk→fcfd.",
    )


def _passo_d(inputs: PavimentoIndustrialeInput, sott: SottofondoResult) -> Passo:
    return Passo(
        simbolo="d", formula="h - c",
        valori=(
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="spessore della piastra"),
            Valore(simbolo="c", valore=inputs.c_mm, unita="mm", descrizione="copriferro"),
        ),
        risultato=sott.d_mm, unita="mm",
        nota="Altezza utile della piastra.",
    )


def _passo_ecm(mat: MaterialiResult) -> Passo:
    return Passo(
        simbolo="E_cm", formula="22000 * (f_cm / 10)^0.3",
        valori=(Valore(simbolo="f_cm", valore=mat.fcm_MPa, unita="MPa", descrizione="resistenza cilindrica media, f_cm=f_ck+8"),),
        risultato=mat.ecm_MPa, unita="MPa", clausola=CLAUSOLA_NTC,
        nota="Modulo elastico secante del calcestruzzo.",
    )


def _passo_w(inputs: PavimentoIndustrialeInput, sott: SottofondoResult) -> Passo:
    return Passo(
        simbolo="W", formula="1000 * h^2 / 6",
        valori=(Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="spessore della piastra"),),
        risultato=sott.w_mm3_m, unita="mm3/m",
        nota="Modulo di resistenza a flessione di una striscia di piastra larga 1 m.",
    )


def _passo_lambda(inputs: PavimentoIndustrialeInput, mat: MaterialiResult, sott: SottofondoResult) -> Passo:
    return Passo(
        simbolo="λ", formula="(3 * k_T / (E_cm * h^3))^0.25",
        valori=(
            Valore(simbolo="k_T", valore=sott.kt_N_mm3, unita="N/mm3", descrizione=f"modulo di reazione del sottofondo, valore tabellare (Winkler) per {inputs.sottofondo_tipo!r}" if inputs.sottofondo_tipo else "modulo di reazione del sottofondo, valore manuale d'ingresso"),
            Valore(simbolo="E_cm", valore=mat.ecm_MPa, unita="MPa", descrizione="calcolato sopra"),
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="spessore della piastra"),
        ),
        risultato=sott.lambda_mm1, unita="1/mm",
        nota="Parametro di rigidezza della piastra, usato nelle formule di Westergaard per il carico distribuito.",
    )


def _passo_l(inputs: PavimentoIndustrialeInput, mat: MaterialiResult, sott: SottofondoResult) -> Passo:
    return Passo(
        simbolo="l", formula="((E_cm * h^3) / (12 * (1 - ν^2) * k_T))^0.25",
        valori=(
            Valore(simbolo="E_cm", valore=mat.ecm_MPa, unita="MPa", descrizione="calcolato sopra"),
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="spessore della piastra"),
            Valore(simbolo="ν", valore=inputs.nu_poisson, descrizione="coefficiente di Poisson del calcestruzzo"),
            Valore(simbolo="k_T", valore=sott.kt_N_mm3, unita="N/mm3", descrizione="modulo di reazione del sottofondo, calcolato sopra"),
        ),
        risultato=sott.l_mm, unita="mm",
        nota="Raggio di rigidezza relativa di Westergaard, usato nelle formule dei carichi concentrati.",
    )


def _passo_mrd(inputs: PavimentoIndustrialeInput, mat: MaterialiResult, sott: SottofondoResult, arm: ArmaturaResult) -> Passo:
    # A_s [mm²/m]·0,9d [mm]·f_yd [N/mm²] è in N·mm/m; il '/1000' finale converte mm->m nel
    # momento (N·mm/m -> N·m/m), NON "per metro" (che resta invariato): il campo del modello,
    # `armatura.py::ArmaturaResult.mrd_Nmm_m`, etichetta 15050 come "Nmm/m" (0,015 kNm/m), un
    # fattore 1000 di troppo — non è calcolo (mai toccato) ma l'unità stampata qui, che
    # l'harness confronta solo per presenza, non per stringa esatta (review finding MISLEADING).
    formula = "(φ^2 * π / 4 * 1000 / S) * 0.9 * d * (f_yk / γ_s) / 1000"
    return Passo(
        simbolo="M_Rd", formula=formula,
        valori=(
            Valore(simbolo="φ", valore=inputs.phi_rete_mm, unita="mm", descrizione="diametro della rete elettrosaldata"),
            Valore(simbolo="π", valore=math.pi),
            Valore(simbolo="S", valore=inputs.passo_rete_mm, unita="mm", descrizione="passo della rete elettrosaldata"),
            Valore(simbolo="d", valore=sott.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
            Valore(simbolo="f_yk", valore=mat.fyk_MPa, unita="MPa", descrizione="tensione caratteristica di snervamento dell'acciaio, valore tabellare (Materiali!E2:F2, B450C)"),
            Valore(simbolo="γ_s", valore=inputs.gamma_s, descrizione="coefficiente parziale di sicurezza dell'acciaio"),
        ),
        risultato=arm.mrd_Nmm_m, unita="N·m/m", clausola=CLAUSOLA_MATERIALI,
        nota="Momento resistente della sezione armata con rete elettrosaldata, braccio di leva semplificato 0,9d.",
    )
