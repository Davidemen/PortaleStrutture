"""Verified restatement (docs/architecture-phase2.md) of `instabilita_flesso_torsionale.py`
(M_cr, λ̄_LT, χ_LT — EN1993-1-1 §6.3.2.2/§6.3.2.3). Φ_LT is folded into χ_LT's own formula (used
only there), same pattern as `relazione_instabilita_flessionale.py::_passo_chi`. I_w and G (used
only inside M_cr's own formula) are cited directly from `Sezione`, with their own defining formula
in the `descrizione`, the way the architecture brief allows for a single-use intermediate. C_1 (the
moment-diagram-shape factor of the 3-factor ECCS Annex F formula) gets its own "lookup only" `Passo`
(review finding MISSING_STEP: it used to be a bare literal inside M_cr's own formula, unlike every
table value in the loads packages, which gets a `Passo`), same pattern as α_yy/α_zz in
`relazione_instabilita_flessionale.py`.

Neither M_cr, λ̄_LT nor χ_LT feeds a `Check` of its own: they feed the interaction of
`relazione_interazione.py` (§6.3.3) only. `verifica_non_necessaria` (§6.3.2.2(4)'s exemption) is
mentioned in χ_LT's `nota`, not restated as its own comparison `Passo` — it carries no UI `symbol`
hint, so the harness does not require it, and NTC2018-style €steps only exist for actual Checks or
values another formula reuses.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import ColonnaEc3Input
from .relazione_comune import PI_GRECO, modulo_flessionale
from .results import ColonnaEc3Output
from .sezione import numero_classe
from .tables import BETA_LT, LAMBDA_LT_0


def traccia_instabilita_torsionale(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Traccia:
    """4 passi: C_1, M_cr, λ̄_LT, χ_LT."""
    return Traccia(
        titolo="Instabilità flesso-torsionale (svergolamento)",
        passi=(_passo_c1(inputs), _passo_mcr(inputs, output), _passo_lambda_lt(inputs, output), _passo_chi_lt(output)),
    )


def _passo_c1(inputs: ColonnaEc3Input) -> Passo:
    return Passo(
        simbolo="C_1", formula="C_1",
        valori=(Valore(simbolo="C_1", valore=inputs.c1, descrizione="fattore del diagramma dei momenti, tabella C1 (ECCS Annex F)"),),
        risultato=inputs.c1, unita="-", clausola="ECCS Annex F, tabella C1",
        nota="Dato d'ingresso: il diagramma dei momenti va scelto dall'ingegnere, non è calcolato qui.",
    )


def _passo_mcr(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    sezione = output.sezione
    return Passo(
        simbolo="M_cr",
        formula="C_1 * (π^2 * E * I_zz / l_T^2) * sqrt(I_w/I_zz + (l_T^2 * G * I_T)/(π^2 * E * I_zz))",
        valori=(
            Valore(simbolo="C_1", valore=inputs.c1, descrizione="calcolato sopra"),
            Valore(simbolo="π", valore=PI_GRECO),
            Valore(simbolo="E", valore=inputs.e_MPa, unita="MPa"),
            Valore(simbolo="I_zz", valore=inputs.izz_mm4, unita="mm4"),
            Valore(simbolo="l_T", valore=inputs.lt_mm, unita="mm", descrizione="lunghezza libera di svergolamento"),
            Valore(simbolo="I_w", valore=sezione.iw_mm6, unita="mm6", descrizione="costante di ingobbamento, I_w=I_zz·(h-t_f)²/4"),
            Valore(simbolo="G", valore=sezione.g_MPa, unita="MPa", descrizione="modulo di elasticità tangenziale, G=E/[2(1+ν)]"),
            Valore(simbolo="I_T", valore=inputs.it_mm4, unita="mm4", descrizione="momento d'inerzia torsionale"),
        ),
        risultato=output.instabilita_torso_flessionale.mcr_Nmm, unita="Nmm",
        clausola="EN1993-1-1 §6.3.2.2, M_cr secondo ECCS Annex F (formula a 3 fattori con C_1)",
        nota="Momento critico elastico per instabilità flesso-torsionale.",
    )


def _passo_lambda_lt(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    classe_num = numero_classe(inputs.classe_sezione)
    simbolo_modulo, modulo = modulo_flessionale(classe_num, inputs.wel_y_mm3, inputs.wpl_y_mm3, "y")
    return Passo(
        simbolo="λ_LT",
        formula=f"sqrt({simbolo_modulo} * f_yk / M_cr)",
        valori=(
            Valore(simbolo=simbolo_modulo, valore=modulo, unita="mm3", descrizione=f"modulo di resistenza (classe {classe_num})"),
            Valore(simbolo="f_yk", valore=output.materiali.fyk_MPa, unita="MPa"),
            Valore(simbolo="M_cr", valore=output.instabilita_torso_flessionale.mcr_Nmm, unita="Nmm", descrizione="calcolato sopra"),
        ),
        risultato=output.instabilita_torso_flessionale.lambda_lt, unita="-", clausola="EN1993-1-1 §6.3.2.2 eq. (6.56)",
        nota="Come per λ_yy/λ_zz, l'eq. (6.56) impiega la resistenza CARATTERISTICA f_yk (M_Rk=W·f_yk).",
    )


def _passo_chi_lt(output: ColonnaEc3Output) -> Passo:
    fi_lt = "(0.5*(1+α_LT*(λ_LT-λ_LT,0)+β_LT*λ_LT^2))"
    non_necessaria = output.instabilita_torso_flessionale.verifica_non_necessaria
    return Passo(
        simbolo="χ_LT",
        formula=f"min(min(1, 1/({fi_lt} + sqrt({fi_lt}^2-β_LT*λ_LT^2))), 1/λ_LT^2)",
        valori=(
            Valore(simbolo="α_LT", valore=output.sezione.alpha_lt, descrizione=f"fattore di imperfezione, curva {output.sezione.curva_instabilita_lt!r} (EN1993-1-1 Tab. 6.3-like)"),
            Valore(simbolo="λ_LT", valore=output.instabilita_torso_flessionale.lambda_lt, descrizione="calcolato sopra"),
            Valore(simbolo="λ_LT,0", valore=LAMBDA_LT_0, descrizione="valore raccomandato, EN1993-1-1 §6.3.2.3"),
            Valore(simbolo="β_LT", valore=BETA_LT, descrizione="valore raccomandato, EN1993-1-1 §6.3.2.3"),
        ),
        risultato=output.instabilita_torso_flessionale.chi_lt, unita="-", clausola="EN1993-1-1 §6.3.2.3 eq. (6.57)",
        nota="Non è una verifica a sé stante: alimenta l'interazione N-My-Mz (§6.3.3). La riduzione LTB "
             f"non è richiesta se λ_LT < λ_LT,0 (qui: {'sì' if non_necessaria else 'no'}), §6.3.2.2(4).",
    )
