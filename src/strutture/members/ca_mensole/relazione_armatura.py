"""Verified restatement of `ca-mensola-tozza`'s reinforcement areas (`armature.py`) step of
docs/architecture-phase2.md §6 wave 2/3. `A_s,hor`/`A_s,incl` are plain bar-area sums (identical
whether `n=0` or not: `n * π/4 * ⌀^2` is zero either way, so no branch is needed to mirror
`rebar_helpers.bars_area_or_zero`'s own `n==0` shortcut). `k_staffe` (`coefficiente_c`) is a
two-value lookup by `staffe_verticali` (SI/NO), restated as a bare-identifier `Passo` per §6's
lookup rule — named `k_staffe`, NOT the bare `c` the model's own `symbol` hint uses
(`models.py::CapacitaResult.c_coeff`, never edited here), because `relazione_materiali_geometria.py`
already uses `c` for the concrete cover in `d = h - c`: two unrelated quantities sharing one symbol
in the same "Sviluppo dei calcoli" (review finding MISLEADING). `A_s,lnk,min` restates ONLY the
branch the calculation actually selected (`a` vs `0.5h`, an UNVERIFIED-against-NTC2018-text
constant pair per docs/divergences/ca-mensole.md "Da verificare": the `nota` says so, per lesson 6
— never paper over a clause that isn't independently confirmed)."""
import math

from strutture.shared.relazione import Passo, Traccia, Valore

from .armature import AS_LNK_FACTOR_LONG_SPAN, AS_LNK_REDUCTION_SHORT_SPAN, HALF_HEIGHT_THRESHOLD
from .capacita import STAFFE_ASSENTI_C, STAFFE_VERTICALI_C
from .models import ArmatureResult, MensolaTozzaInput

NOTA_COSTANTI_NON_VERIFICATE = (
    "Le costanti del modello puntone-tirante non sono verificate indipendentemente contro il "
    "testo NTC2018 (docs/divergences/ca-mensole.md, 'Da verificare')."
)
# `capacita.py::STAFFE_VERTICALI_C`/`STRUT_EFFECTIVENESS_COEFF` sono commentate "clausola '?'" nel
# codice: nessuna delle due ha una provenienza normativa identificata (review finding WRONG_CLAUSE
# — la traccia non può citare NTC2018 §4.1.6.1.3 / EN 1992-1-1 §6.5, che per il puntone dà una
# formula diversa e non prevede alcun bonus per staffe verticali).
CLAUSOLA_EMPIRICA = "formula empirica — clausola non identificata (docs/divergences/ca-mensole.md)"


def traccia_armatura(inputs: MensolaTozzaInput, armature: ArmatureResult, fyd_MPa: float) -> Traccia:
    """4 passi: A_s,hor, A_s,incl, k_staffe (lookup), A_s,lnk,min (solo il ramo selezionato)."""
    return Traccia(
        titolo="Armatura",
        passi=(
            _passo_as_hor(inputs, armature.as_hor_mm2),
            _passo_as_incl(inputs, armature.as_incl_mm2),
            _passo_c_coeff(inputs),
            _passo_as_lnk_min(inputs, armature, fyd_MPa),
        ),
    )


def _passo_as_hor(inputs: MensolaTozzaInput, as_hor_mm2: float) -> Passo:
    return Passo(
        simbolo="A_s,hor", formula="n_hor * π/4 * φ_hor^2",
        valori=(
            Valore(simbolo="n_hor", valore=inputs.n_hor, descrizione="numero di ferri orizzontali (tiranti)"),
            Valore(simbolo="φ_hor", valore=inputs.phi_hor_mm, unita="mm", descrizione="diametro dei ferri orizzontali"),
            Valore(simbolo="π", valore=math.pi, descrizione="pi greco"),
        ),
        risultato=as_hor_mm2, unita="mm2", nota="Area di armatura orizzontale (tiranti).",
    )


def _passo_as_incl(inputs: MensolaTozzaInput, as_incl_mm2: float) -> Passo:
    return Passo(
        simbolo="A_s,incl", formula="n_incl * π/4 * φ_incl^2",
        valori=(
            Valore(simbolo="n_incl", valore=inputs.n_incl, descrizione="numero di ferri inclinati"),
            Valore(simbolo="φ_incl", valore=inputs.phi_incl_mm, unita="mm", descrizione="diametro dei ferri inclinati"),
            Valore(simbolo="π", valore=math.pi, descrizione="pi greco"),
        ),
        risultato=as_incl_mm2, unita="mm2", nota="Area di armatura inclinata (0 se assente).",
    )


def _passo_c_coeff(inputs: MensolaTozzaInput) -> Passo:
    # La condizione che seleziona il valore va nel simbolo stampato, non solo nella nota:
    # `traccia_a_testo` non stampa mai `Passo.nota` (review finding MISSING_STEP).
    valore = STAFFE_VERTICALI_C if inputs.staffe_verticali == "SI" else STAFFE_ASSENTI_C
    simbolo = f"k_staffe  (staffe verticali: {inputs.staffe_verticali})"
    return Passo(
        simbolo=simbolo, formula="k_staffe",
        valori=(Valore(simbolo="k_staffe", valore=valore, descrizione=f"coefficiente di amplificazione, staffe verticali = '{inputs.staffe_verticali}'"),),
        risultato=valore, unita="-", clausola=CLAUSOLA_EMPIRICA,
        nota=f"{NOTA_COSTANTI_NON_VERIFICATE} Vale {STAFFE_VERTICALI_C:g} se presenti staffe verticali, {STAFFE_ASSENTI_C:g} altrimenti.",
    )


def _passo_as_lnk_min(inputs: MensolaTozzaInput, armature: ArmatureResult, fyd_MPa: float) -> Passo:
    campata_corta = inputs.a_mm < HALF_HEIGHT_THRESHOLD * inputs.h_mm
    if campata_corta:
        formula = f"{AS_LNK_REDUCTION_SHORT_SPAN:g} * A_s,hor"
        valori = (Valore(simbolo="A_s,hor", valore=armature.as_hor_mm2, unita="mm2", descrizione="armatura orizzontale, calcolata sopra"),)
        nota_ramo = f"Ramo a < 0,5h selezionato (a={inputs.a_mm:g} mm, 0,5h={0.5 * inputs.h_mm:g} mm)."
    else:
        formula = f"{AS_LNK_FACTOR_LONG_SPAN:g} * P_Ed * 1000 / f_yd"
        valori = (
            Valore(simbolo="P_Ed", valore=inputs.ped_kN, unita="kN", descrizione="carico verticale di progetto"),
            Valore(simbolo="f_yd", valore=fyd_MPa, unita="MPa", descrizione="tensione di calcolo di snervamento dell'acciaio, calcolata sopra"),
        )
        nota_ramo = f"Ramo a ≥ 0,5h selezionato (a={inputs.a_mm:g} mm, 0,5h={0.5 * inputs.h_mm:g} mm)."
    return Passo(
        simbolo="A_s,lnk,min", formula=formula, valori=valori, risultato=armature.as_lnk_min_mm2, unita="mm2",
        nota=f"{nota_ramo} {NOTA_COSTANTI_NON_VERIFICATE} (continuità fra i due rami non verificata, "
             "docs/divergences/ca-mensole.md).",
    )
