"""Verified restatement of `ca-mensola-tozza`'s strut-and-tie capacities (`capacita.py`) and
verdict `Check`s (`verifica.py`) steps of docs/architecture-phase2.md §6 wave 2/3 — NTC2018
§4.1.6.1.3 (mensole tozze) / EN 1992-1-1 §6.5 (strut-and-tie method): tie force `P_Rs`, strut
capacity `P_Rc`, the inclined-bar contribution `ΔP_R`, the global capacity `P_R = P_Rs + 0.8·ΔP_R`
(highlighted output), the ductile-failure hierarchy Check, the ULS Check and the horizontal
stirrup (node) Check. The strut-and-tie constants (0,4; 0,8; 0,9) are the model's own coefficients,
NOT independently verified against the NTC2018 text (docs/divergences/ca-mensole.md "Da
verificare"): every `Passo` that uses one says so in its `nota`, per lesson 6 (restate what the
code does, never paper over an unconfirmed clause). `P_Rc` is the ONE exception to the shared
`CLAUSOLA` citation: `capacita.py` itself comments `STRUT_EFFECTIVENESS_COEFF`/`STAFFE_VERTICALI_C`
"clausola '?'" — no identified normative source, and EN 1992-1-1 §6.5 gives strut strength as
σ_Rd,max=0,6·ν'·f_cd on the node/strut area, a different formula with no 50% bonus for vertical
stirrups. Citing "NTC2018 §4.1.6.1.3 / EN 1992-1-1 §6.5" on that row would dress an empirical
coefficient as normative (review finding WRONG_CLAUSE): it uses `CLAUSOLA_EMPIRICA` instead, like
the `k_staffe` lookup it depends on (`relazione_armatura.py::_passo_c_coeff`)."""
import math

from strutture.shared.relazione import Passo, Traccia, Valore

from .capacita import INCLINED_CONTRIBUTION_REDUCTION, LEVER_ARM_FACTOR, STRUT_EFFECTIVENESS_COEFF
from .models import ArmatureResult, CapacitaResult, GeometriaResult, MaterialiResult, MensolaTozzaInput
from .relazione_armatura import CLAUSOLA_EMPIRICA
from .verifica import STIRRUP_LEGS

CLAUSOLA = "NTC2018 §4.1.6.1.3 / EN 1992-1-1 §6.5"
NOTA_COSTANTI_NON_VERIFICATE = (
    "Le costanti del modello puntone-tirante non sono verificate indipendentemente contro il "
    "testo NTC2018 (docs/divergences/ca-mensole.md, 'Da verificare')."
)


def traccia_capacita(
    inputs: MensolaTozzaInput, materiali: MaterialiResult, geometria: GeometriaResult,
    armature: ArmatureResult, capacita: CapacitaResult,
) -> Traccia:
    """5 passi: P_Rs (tirante), P_Rc (puntone), Check gerarchia, ΔP_R, P_R (evidenziato)."""
    return Traccia(
        titolo="Capacità portante (modello a bielle e tiranti)",
        passi=(
            _passo_prs(inputs, materiali, geometria, armature, capacita.prs_kN),
            _passo_prc(inputs, materiali, geometria, capacita),
            _passo_check_gerarchia(capacita),
            _passo_dpr(inputs, materiali, armature, capacita.dpr_kN),
            _passo_pr(capacita),
        ),
    )


def _passo_prs(
    inputs: MensolaTozzaInput, materiali: MaterialiResult, geometria: GeometriaResult,
    armature: ArmatureResult, prs_kN: float,
) -> Passo:
    return Passo(
        simbolo="P_Rs", formula=f"(A_s,hor * f_yd - H_Ed * 1000) * {LEVER_ARM_FACTOR:g} * d / l",
        valori=(
            Valore(simbolo="A_s,hor", valore=armature.as_hor_mm2, unita="mm2", descrizione="armatura orizzontale, calcolata sopra"),
            Valore(simbolo="f_yd", valore=materiali.fyd_MPa, unita="MPa", descrizione="tensione di calcolo di snervamento dell'acciaio, calcolata sopra"),
            Valore(simbolo="H_Ed", valore=inputs.hed_kN, unita="kN", descrizione="carico orizzontale di progetto"),
            Valore(simbolo="d", valore=geometria.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
            Valore(simbolo="l", valore=geometria.l_mm, unita="mm", descrizione="braccio di taglio equivalente, calcolato sopra"),
        ),
        risultato=prs_kN, unita="kN", scala=1e-3, clausola=CLAUSOLA,
        nota=f"Capacità lato acciaio (tirante). {NOTA_COSTANTI_NON_VERIFICATE}",
    )


def _passo_prc(inputs: MensolaTozzaInput, materiali: MaterialiResult, geometria: GeometriaResult, capacita: CapacitaResult) -> Passo:
    return Passo(
        simbolo="P_Rc",
        formula=f"{STRUT_EFFECTIVENESS_COEFF:g} * b * d * f_cd * k_staffe / (1 + (l / ({LEVER_ARM_FACTOR:g} * d))^2)",
        valori=(
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm", descrizione="larghezza della mensola"),
            Valore(simbolo="d", valore=geometria.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
            Valore(simbolo="f_cd", valore=materiali.fcd_MPa, unita="MPa", descrizione="resistenza di calcolo a compressione del calcestruzzo, calcolata sopra"),
            Valore(simbolo="k_staffe", valore=capacita.c_coeff, descrizione="coefficiente di amplificazione per staffe verticali, calcolato sopra"),
            Valore(simbolo="l", valore=geometria.l_mm, unita="mm", descrizione="braccio di taglio equivalente, calcolato sopra"),
        ),
        risultato=capacita.prc_kN, unita="kN", scala=1e-3, clausola=CLAUSOLA_EMPIRICA,
        nota=f"Capacità lato calcestruzzo (puntone compresso). {NOTA_COSTANTI_NON_VERIFICATE}",
    )


def _passo_check_gerarchia(capacita: CapacitaResult) -> Passo:
    soddisfatta = capacita.prs_kN <= capacita.prc_kN
    return Passo(
        simbolo="P_Rs ≤ P_Rc", formula="P_Rs <= P_Rc",
        valori=(
            Valore(simbolo="P_Rs", valore=capacita.prs_kN, unita="kN", descrizione="capacità lato acciaio, calcolata sopra"),
            Valore(simbolo="P_Rc", valore=capacita.prc_kN, unita="kN", descrizione="capacità lato calcestruzzo, calcolata sopra"),
        ),
        risultato=capacita.prs_kN, unita="kN", clausola=CLAUSOLA,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Gerarchia delle resistenze: rottura duttile lato acciaio (la crisi del puntone di calcestruzzo è fragile).",
    )


def _passo_dpr(inputs: MensolaTozzaInput, materiali: MaterialiResult, armature: ArmatureResult, dpr_kN: float) -> Passo:
    return Passo(
        simbolo="ΔP_R", formula="A_s,incl * f_yd * sin(α)",
        valori=(
            Valore(simbolo="A_s,incl", valore=armature.as_incl_mm2, unita="mm2", descrizione="armatura inclinata, calcolata sopra"),
            Valore(simbolo="f_yd", valore=materiali.fyd_MPa, unita="MPa"),
            Valore(simbolo="α", valore=inputs.angolo_incl_deg, unita="°", descrizione="inclinazione dell'armatura inclinata"),
        ),
        risultato=dpr_kN, unita="kN", scala=1e-3, clausola=CLAUSOLA,
        nota="Contributo alla capacità dell'armatura inclinata (0 se assente).",
    )


def _passo_pr(capacita: CapacitaResult) -> Passo:
    return Passo(
        simbolo="P_R", formula=f"min(P_Rs + {INCLINED_CONTRIBUTION_REDUCTION:g} * ΔP_R, P_Rc)",
        valori=(
            Valore(simbolo="P_Rs", valore=capacita.prs_kN, unita="kN", descrizione="capacità lato acciaio, calcolata sopra"),
            Valore(simbolo="ΔP_R", valore=capacita.dpr_kN, unita="kN", descrizione="contributo dell'armatura inclinata, calcolato sopra"),
            Valore(simbolo="P_Rc", valore=capacita.prc_kN, unita="kN", descrizione="capacità del puntone di calcestruzzo, calcolata sopra: limita la capacità globale"),
        ),
        risultato=capacita.pr_kN, unita="kN", clausola=CLAUSOLA,
        nota=f"Capacità portante globale della mensola. {NOTA_COSTANTI_NON_VERIFICATE}",
    )


def traccia_verifiche(inputs: MensolaTozzaInput, capacita: CapacitaResult, armature: ArmatureResult) -> Traccia:
    """3 passi: Check ULS (P_Ed < P_R), A_s,staffe (derivazione), Check staffe orizzontali."""
    as_staffe_mm2 = STIRRUP_LEGS * inputs.n_staffe * math.pi / 4.0 * inputs.phi_staffe_mm**2
    uls_passed = capacita.pr_kN > inputs.ped_kN
    staffe_passed = as_staffe_mm2 >= armature.as_lnk_min_mm2
    return Traccia(
        titolo="Verifiche",
        passi=(
            _passo_check_uls(inputs, capacita, uls_passed),
            _passo_as_staffe(inputs, as_staffe_mm2),
            _passo_check_staffe(as_staffe_mm2, armature.as_lnk_min_mm2, staffe_passed),
        ),
    )


def _passo_check_uls(inputs: MensolaTozzaInput, capacita: CapacitaResult, soddisfatta: bool) -> Passo:
    return Passo(
        simbolo="P_Ed < P_R", formula="P_Ed < P_R",
        valori=(
            Valore(simbolo="P_Ed", valore=inputs.ped_kN, unita="kN", descrizione="carico verticale di progetto"),
            Valore(simbolo="P_R", valore=capacita.pr_kN, unita="kN", descrizione="capacità portante globale, calcolata sopra"),
        ),
        risultato=inputs.ped_kN, unita="kN", clausola=CLAUSOLA,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Verifica allo stato limite ultimo.",
    )


def _passo_as_staffe(inputs: MensolaTozzaInput, as_staffe_mm2: float) -> Passo:
    return Passo(
        simbolo="A_s,staffe", formula=f"{STIRRUP_LEGS:g} * n_staffe * π/4 * φ_sw^2",
        valori=(
            Valore(simbolo="n_staffe", valore=inputs.n_staffe, descrizione="numero di staffe orizzontali"),
            Valore(simbolo="φ_sw", valore=inputs.phi_staffe_mm, unita="mm", descrizione="diametro delle staffe orizzontali"),
            Valore(simbolo="π", valore=math.pi, descrizione="pi greco"),
        ),
        risultato=as_staffe_mm2, unita="mm2",
        nota=f"Area delle staffe orizzontali presenti ({STIRRUP_LEGS:g} bracci a staffa, staffa chiusa).",
    )


def _passo_check_staffe(as_staffe_mm2: float, as_lnk_min_mm2: float, soddisfatta: bool) -> Passo:
    return Passo(
        simbolo="A_s,staffe ≥ A_s,lnk,min", formula="A_s,staffe >= A_s,lnk,min",
        valori=(
            Valore(simbolo="A_s,staffe", valore=as_staffe_mm2, unita="mm2", descrizione="area delle staffe orizzontali, calcolata sopra"),
            Valore(simbolo="A_s,lnk,min", valore=as_lnk_min_mm2, unita="mm2", descrizione="area minima di staffe/tiranti orizzontali richiesta, calcolata sopra"),
        ),
        risultato=as_staffe_mm2, unita="mm2", clausola=CLAUSOLA,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Verifica nodale: le staffe orizzontali (o il tirante) devono coprire l'area minima richiesta.",
    )
