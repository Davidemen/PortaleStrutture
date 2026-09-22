"""Verified restatement of `ca-apertura-fessure` (docs/architecture-phase2.md §6, wave 2/3
adoption) — Circ. 2019 §C4.1.2.2.4.5 (crack spacing) / EN 1992-1-1 §7.3.4 (mean strain, crack
width): geometry and materials/coefficients live in `relazione_apertura_fessure_geometria.py`
(this module assembles them with the remaining three traces — spacing, mean strain, crack
width). `Δs_m` restates ONLY the branch (`C4.1.7`/`C4.1.10`) the calculation actually selected
(`spaziatura_fessure.ramo_spaziatura`, an `interferro < s_lim` comparison the tool itself never
turns into a `Check`): the `nota` states which branch and why, per docs/architecture-phase2.md
§6 lesson 4 ("an informative ratio that is NOT a normative check must say so"). `w_lim` is a Tab.
4.1.IV lookup; `utilizzo` (`w_k/w_lim`, rounded UP to 2 decimals by `math.ceil`) has no closed
form in the notation grammar (no rounding function, docs/architecture-phase2.md §2) — restated as
a bare-identifier `Passo`, the value read directly off the calculation, per §6's lookup rule.

18 passi across 5 `Traccia` (6 geometry + 8 materials + 2 spacing + 1 strain + 1 crack-width
Check + 1 informative utilisation), covering the tool's single `Check` and both its highlighted
outputs (`w_k`, `w_k/w_lim`)."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .ampiezza_fessura import FATTORE_AMPIEZZA_FESSURA
from .deformazione_media import COEFF_DEFORMAZIONE_MINIMA
from .models import AperturaFessureInput, AperturaFessureOutput, RisultatoFessurazioneOutput
from .relazione_apertura_fessure_geometria import traccia_geometria, traccia_materiali
from .spaziatura_fessure import FATTORE_DIVISIONE_C4_1_7, FATTORE_SPAZIATURA_LIMITE

CLAUSOLA_SPAZIATURA = "Circ. 2019 §C4.1.7 / EN 1992-1-1 §7.3.4 eq. (7.11)"
CLAUSOLA_SPAZIATURA_C4_1_10 = "Circ. 2019 §C4.1.10 / EN 1992-1-1 §7.3.4 eq. (7.14)"
CLAUSOLA_DEFORMAZIONE = "EN 1992-1-1 §7.3.4"
CLAUSOLA_APERTURA = "Circ. 2019 §C4.1.2.2.4.5 / EN 1992-1-1 §7.3.4"


def relazione_apertura_fessure(inputs: AperturaFessureInput, output: AperturaFessureOutput) -> tuple[Traccia, ...]:
    return (
        traccia_geometria(inputs, output),
        traccia_materiali(inputs, output),
        _traccia_spaziatura(inputs, output),
        _traccia_deformazione(inputs, output),
        _traccia_apertura(inputs, output),
    )


def _traccia_spaziatura(inputs: AperturaFessureInput, output: AperturaFessureOutput) -> Traccia:
    """2 passi: s_lim, Δs_m,eff (solo il ramo selezionato)."""
    geometria, fessurazione = output.geometria, output.fessurazione
    return Traccia(
        titolo="Spaziatura media delle fessure",
        passi=(_passo_slim(inputs, geometria.phi_eq_mm, fessurazione.slim_mm), _passo_delta_sm(inputs, output)),
    )


def _passo_slim(inputs: AperturaFessureInput, phi_eq_mm: float, slim_mm: float) -> Passo:
    return Passo(
        simbolo="s_lim", formula=f"{FATTORE_SPAZIATURA_LIMITE:g} * (c + φ_eq / 2)",
        valori=(
            Valore(simbolo="c", valore=inputs.copriferro_mm, unita="mm", descrizione="copriferro dell'armatura"),
            Valore(simbolo="φ_eq", valore=phi_eq_mm, unita="mm", descrizione="diametro equivalente delle barre, calcolato sopra"),
        ),
        risultato=slim_mm, unita="mm", clausola="Circ. 2019 §C4.1.7",
        nota="Soglia di applicabilità: sotto questa spaziatura fra le barre si usa il ramo §C4.1.7, sopra il ramo §C4.1.10.",
    )


def _passo_delta_sm(inputs: AperturaFessureInput, output: AperturaFessureOutput) -> Passo:
    geometria, fessurazione, coefficienti = output.geometria, output.fessurazione, output.coefficienti
    ramo_c4_1_7 = fessurazione.ramo == "C4.1.7"
    nota_ramo = (
        f"Ramo §C4.1.7 selezionato: interferro s={inputs.interferro_mm:g} mm < s_lim={fessurazione.slim_mm:.1f} mm."
        if ramo_c4_1_7 else
        f"Ramo §C4.1.10 selezionato: interferro s={inputs.interferro_mm:g} mm ≥ s_lim={fessurazione.slim_mm:.1f} mm "
        "(spaziatura non ravvicinata: la distanza media fra le fessure dipende solo da h e x)."
    )
    # Il ramo selezionato (interferro confrontato con s_lim, calcolato sopra) va nel simbolo
    # stampato, non solo nella nota (`traccia_a_testo` non stampa mai `Passo.nota`, review finding
    # MISSING_STEP): altrimenti s_lim resta un valore stampato e mai più riusato in modo visibile.
    if ramo_c4_1_7:
        simbolo = "Δs_m  (§C4.1.7: interferro < s_lim)"
        formula = f"(k_3 * c + k_1 * k_2 * k_4 * φ_eq / ρ_eff) / {FATTORE_DIVISIONE_C4_1_7:g}"
        valori = (
            Valore(simbolo="k_3", valore=inputs.k3, descrizione="costante di spaziatura delle fessure"),
            Valore(simbolo="c", valore=inputs.copriferro_mm, unita="mm"),
            Valore(simbolo="k_1", valore=coefficienti.k1, descrizione="coefficiente di aderenza, calcolato sopra"),
            Valore(simbolo="k_2", valore=coefficienti.k2, descrizione="coefficiente per tipo di sollecitazione, calcolato sopra"),
            Valore(simbolo="k_4", valore=inputs.k4, descrizione="costante di spaziatura delle fessure"),
            Valore(simbolo="φ_eq", valore=geometria.phi_eq_mm, unita="mm", descrizione="diametro equivalente, calcolato sopra"),
            Valore(simbolo="ρ_eff", valore=geometria.rho_eff, descrizione="rapporto di armatura efficace, calcolato sopra"),
        )
        clausola = CLAUSOLA_SPAZIATURA
    else:
        simbolo = "Δs_m  (§C4.1.10: interferro ≥ s_lim)"
        formula = "(1.3 / 1.7) * (h - x)"
        valori = (
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm"),
            Valore(simbolo="x", valore=inputs.x_mm, unita="mm", descrizione="profondità dell'asse neutro"),
        )
        clausola = CLAUSOLA_SPAZIATURA_C4_1_10
    return Passo(
        simbolo=simbolo, formula=formula, valori=valori, risultato=fessurazione.delta_sm_mm, unita="mm",
        clausola=clausola, nota=nota_ramo,
    )


def _traccia_deformazione(inputs: AperturaFessureInput, output: AperturaFessureOutput) -> Traccia:
    """1 passo: ε_sm."""
    geometria, materiale, coefficienti, fessurazione = output.geometria, output.materiale, output.coefficienti, output.fessurazione
    return Traccia(
        titolo="Deformazione media dell'armatura",
        passi=(
            Passo(
                simbolo="ε_sm",
                formula=f"max((σ_s - k_t * f_ctm / ρ_eff * (1 + α_e * ρ_eff)) / E_s, {COEFF_DEFORMAZIONE_MINIMA:g} * σ_s / E_s)",
                valori=(
                    Valore(simbolo="σ_s", valore=inputs.sigma_s_MPa, unita="MPa", descrizione="tensione nell'armatura tesa nella sezione fessurata"),
                    Valore(simbolo="k_t", valore=coefficienti.kt, descrizione="coefficiente per durata del carico, calcolato sopra"),
                    Valore(simbolo="f_ctm", valore=materiale.fctm_MPa, unita="MPa", descrizione="resistenza media a trazione, calcolata sopra"),
                    Valore(simbolo="ρ_eff", valore=geometria.rho_eff, descrizione="rapporto di armatura efficace, calcolato sopra"),
                    Valore(simbolo="α_e", valore=materiale.alpha_e, descrizione="rapporto di omogeneizzazione, calcolato sopra"),
                    Valore(simbolo="E_s", valore=inputs.es_MPa, unita="MPa", descrizione="modulo elastico dell'acciaio"),
                ),
                risultato=fessurazione.epsilon_sm, unita="-", clausola=CLAUSOLA_DEFORMAZIONE,
                nota="Deformazione media dell'armatura, con tension-stiffening; mai minore dello 0,6·σs/Es (limite inferiore).",
            ),
        ),
    )


def _traccia_apertura(inputs: AperturaFessureInput, output: AperturaFessureOutput) -> Traccia:
    """4 passi: w_k, w_lim (lookup), Check w_k<=w_lim, w_k/w_lim (informativo, non un Check)."""
    fessurazione = output.fessurazione
    return Traccia(
        titolo="Apertura delle fessure",
        passi=(
            _passo_wk(fessurazione),
            _passo_wlim(inputs, fessurazione.wlim_mm),
            _passo_check_wk(fessurazione),
            _passo_utilizzo(fessurazione),
        ),
    )


def _passo_wk(fessurazione: RisultatoFessurazioneOutput) -> Passo:
    return Passo(
        simbolo="w_k", formula=f"{FATTORE_AMPIEZZA_FESSURA:g} * ε_sm * Δs_m",
        valori=(
            Valore(simbolo="ε_sm", valore=fessurazione.epsilon_sm, descrizione="deformazione media dell'armatura, calcolata sopra"),
            Valore(simbolo="Δs_m", valore=fessurazione.delta_sm_mm, unita="mm", descrizione="distanza media fra le fessure, calcolata sopra"),
        ),
        risultato=fessurazione.wk_mm, unita="mm", clausola=CLAUSOLA_APERTURA,
        nota="Ampiezza caratteristica delle fessure.",
    )


def _passo_wlim(inputs: AperturaFessureInput, wlim_mm: float) -> Passo:
    return Passo(
        simbolo="w_lim", formula="w_lim",
        valori=(Valore(simbolo="w_lim", valore=wlim_mm, unita="mm", descrizione=f"limite per la classe di fessurazione '{inputs.classe_fessurazione}'"),),
        risultato=wlim_mm, unita="mm", nota="Lettura di NTC2018 Tab. 4.1.IV per la classe di apertura fessura scelta.",
    )


def _passo_check_wk(fessurazione: RisultatoFessurazioneOutput) -> Passo:
    return Passo(
        simbolo="w_k ≤ w_lim", formula="w_k <= w_lim",
        valori=(
            Valore(simbolo="w_k", valore=fessurazione.wk_mm, unita="mm", descrizione="ampiezza caratteristica delle fessure, calcolata sopra"),
            Valore(simbolo="w_lim", valore=fessurazione.wlim_mm, unita="mm", descrizione="limite tabellare, calcolato sopra"),
        ),
        risultato=fessurazione.wk_mm, unita="mm", clausola=CLAUSOLA_APERTURA,
        esito="soddisfatta" if fessurazione.verificato else "non soddisfatta",
        nota="Verifica di apertura delle fessure.",
    )


def _passo_utilizzo(fessurazione: RisultatoFessurazioneOutput) -> Passo:
    return Passo(
        simbolo="w_k/w_lim", formula="u",
        valori=(Valore(simbolo="u", valore=fessurazione.utilizzo, unita="-", descrizione="w_k/w_lim, arrotondato per eccesso a 2 decimali"),),
        risultato=fessurazione.utilizzo, unita="-",
        nota="Tasso di sfruttamento informativo (non un Check separato: la verifica è il confronto "
             "w_k ≤ w_lim sopra); l'arrotondamento per eccesso non ha una forma chiusa nella notazione "
             "(nessuna funzione di arrotondamento nella grammatica, docs/architecture-phase2.md §2), "
             "quindi il valore è riportato direttamente dal calcolo anziché da una formula.",
    )
