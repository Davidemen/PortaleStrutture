"""Verified restatement of `ca-mensola-tozza`'s materials (`materiali.py`, NTC2018 §4.1.2.1.1.1,
Tab. 4.1.V) and geometry (`geometria.py`) steps of docs/architecture-phase2.md §6 wave 2/3.
`γ_s`/`γ_c` are the standard partial-safety factors (not derived, cited directly as `Valore` per
`GAMMA_S`/`GAMMA_C`, the same way `f_ck` is cited in `ca_fessurazione` lookups). `a/d` is an
INFORMATIVE ratio only — NTC2018 §4.1.6.1.3 defines a "mensola tozza" by `a/d ≤ 1` but the
calculation itself never turns this into a `Check` (no branch depends on it): the `Passo`'s
`nota` says so explicitly, per docs/architecture-phase2.md §6 lesson 4."""
from strutture.shared.materials.concrete import ALPHA_CC
from strutture.shared.relazione import Passo, Traccia, Valore

from .geometria import SHEAR_SPAN_OFFSET_COEFF
from .models import GeometriaResult, MaterialiResult, MensolaTozzaInput

CLAUSOLA_MATERIALI = "NTC2018 §4.1.2.1.1.1"


def traccia_materiali(inputs: MensolaTozzaInput, materiali: MaterialiResult) -> Traccia:
    """2 passi: f_yd, f_cd (γ_s/γ_c citati come Valore in ciascuno, Tab. 4.1.V)."""
    return Traccia(
        titolo="Materiali",
        passi=(_passo_fyd(materiali), _passo_fcd(inputs, materiali)),
    )


def _passo_fyd(materiali: MaterialiResult) -> Passo:
    return Passo(
        simbolo="f_yd", formula="f_yk / γ_s",
        valori=(
            Valore(simbolo="f_yk", valore=materiali.fyd_MPa * materiali.gamma_s, unita="MPa", descrizione="tensione caratteristica di snervamento dell'acciaio"),
            Valore(simbolo="γ_s", valore=materiali.gamma_s, descrizione="coefficiente parziale dell'acciaio, Tab. 4.1.V"),
        ),
        risultato=materiali.fyd_MPa, unita="MPa", clausola=CLAUSOLA_MATERIALI,
        nota="Tensione di calcolo di snervamento dell'acciaio.",
    )


def _passo_fcd(inputs: MensolaTozzaInput, materiali: MaterialiResult) -> Passo:
    fck_MPa = materiali.fcd_MPa * materiali.gamma_c / ALPHA_CC
    return Passo(
        simbolo="f_cd", formula=f"{ALPHA_CC:g} * f_ck / γ_c",
        valori=(
            Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa", descrizione=f"resistenza cilindrica caratteristica per la classe {inputs.calcestruzzo}"),
            Valore(simbolo="γ_c", valore=materiali.gamma_c, descrizione="coefficiente parziale del calcestruzzo, Tab. 4.1.V"),
        ),
        risultato=materiali.fcd_MPa, unita="MPa", clausola=CLAUSOLA_MATERIALI,
        nota="Resistenza di calcolo a compressione del calcestruzzo.",
    )


def traccia_geometria(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Traccia:
    """3 passi: d, l, a/d (informativo)."""
    return Traccia(
        titolo="Geometria della mensola",
        passi=(_passo_d(inputs, geometria), _passo_l(inputs, geometria), _passo_a_su_d(inputs, geometria)),
    )


def _passo_d(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Passo:
    return Passo(
        simbolo="d", formula="h - c",
        valori=(
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="altezza della mensola"),
            Valore(simbolo="c", valore=inputs.c_mm, unita="mm", descrizione="copriferro, misurato all'asse delle barre"),
        ),
        risultato=geometria.d_mm, unita="mm", nota="Altezza utile della sezione.",
    )


def _passo_l(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Passo:
    return Passo(
        simbolo="l", formula=f"a + {SHEAR_SPAN_OFFSET_COEFF:g} * d",
        valori=(
            Valore(simbolo="a", valore=inputs.a_mm, unita="mm", descrizione="distanza del carico dal filo del pilastro"),
            Valore(simbolo="d", valore=geometria.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
        ),
        risultato=geometria.l_mm, unita="mm",
        nota="Braccio di taglio equivalente (le costanti del modello puntone-tirante non sono "
             "verificate indipendentemente contro il testo NTC2018, vedi docs/divergences/ca-mensole.md).",
    )


def _passo_a_su_d(inputs: MensolaTozzaInput, geometria: GeometriaResult) -> Passo:
    return Passo(
        simbolo="a/d", formula="a / d",
        valori=(
            Valore(simbolo="a", valore=inputs.a_mm, unita="mm"),
            Valore(simbolo="d", valore=geometria.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
        ),
        risultato=inputs.a_mm / geometria.d_mm, unita="-", clausola="NTC2018 §4.1.6.1.3",
        nota="Rapporto informativo (NON un Check: il calcolo non lo verifica esplicitamente): "
             "NTC2018 §4.1.6.1.3 definisce 'mensola tozza' per a/d ≲ 1, il campo di validità del "
             "modello a bielle e tiranti applicato di seguito.",
    )
