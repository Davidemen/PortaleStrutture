"""Verified restatement (docs/architecture-phase2.md) of `taglio_instabilita.py` (web shear
buckling, EN1993-1-5 §5, column-check!AC27-O75). The web/flange contributions V_bw,Rd and V_bf,Rd
and the cap V_bw,Rd,max are each cited as a single named `Valore` (EN1993-1-5 eq. 5.2/5.3/5.4a),
computed by calling the package's OWN step functions (never re-derived in notation: eq. (5.4a)'s
own c-factor alone chains 4 further sub-formulas) — the way the architecture brief allows for an
intermediate the output model does not expose, mirroring how `ca_travi.relazione_sle` cites
σ_s,limite (a Tab. C4.1.II lookup) directly. Standard mode only: ε/η always key on the CHARACTERISTIC
f_yk (`taglio_instabilita.py`'s own fixed-mode behaviour; the legacy sheet keys on f_yd instead, a
divergence already fixed and documented there, not repeated here).

`richiede_verifica` (hw/t vs. the limit) is not itself one of the package's 11 `Check`: it is the
condition that TRIGGERS this whole verification (EN1993-1-5 §5.1(2)), restated here as an
informative comparison `Passo` (its own title says so) rather than silently assumed.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import ColonnaEc3Input
from .results import ColonnaEc3Output
from .tables import FATTORE_LIMITE_HW_T
from .taglio_instabilita import (
    cw as calcola_cw,
)
from .taglio_instabilita import (
    epsilon,
    eta,
    fattore_c67_flangia,
    fattore_riduzione_ali,
    lambda_w,
    larghezza_efficace_ala_mm,
    momento_resistente_ali_kNm,
    vbf_rd_kN,
    vbw_rd_kN,
    vbw_rd_max_kN,
)


def traccia_taglio_instabilita(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Traccia:
    """4 passi: h_w/t_w (soglia informativa, non è una verifica di sicurezza), λ_w, χ_w (componenti
    di V_bw,Rd), V_b,Rd (Check)."""
    return Traccia(
        titolo="Instabilità per taglio dell'anima — h_w/t_w non è una verifica di sicurezza ma la "
               "soglia che attiva la verifica",
        passi=(
            _passo_hw_t(inputs, output), _passo_lambda_w(inputs, output), _passo_chi_w(inputs, output),
            _passo_vb_rd(inputs, output),
        ),
    )


def _passo_hw_t(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    # `h_w/t_w > limite` è la condizione che ATTIVA la verifica (EN1993-1-5 §5.1(2)), non una
    # verifica essa stessa: stamparla come "soddisfatta" quando SUPERA il limite (il caso
    # sfavorevole, verifica richiesta) la farebbe leggere come un esito positivo (review finding
    # MISLEADING). Il confronto è quindi stampato come "<=" (limite rispettato): "soddisfatta"
    # significa che l'anima NON è snella e la verifica di instabilità a taglio non è necessaria.
    fyk = output.materiali.fyk_MPa
    et = eta(fyk)
    taglio_instab = output.taglio_instabilita
    return Passo(
        simbolo="h_w/t_w",
        formula=f"(h - 2*t_f)/t_w <= {FATTORE_LIMITE_HW_T:g} * sqrt(235/f_yk) / η",
        valori=(
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm"),
            Valore(simbolo="t_f", valore=inputs.tf_mm, unita="mm"),
            Valore(simbolo="t_w", valore=inputs.tw_mm, unita="mm"),
            Valore(simbolo="f_yk", valore=fyk, unita="MPa"),
            Valore(simbolo="η", valore=et, descrizione="η=1 se f_yk>460 MPa, altrimenti 1,2 — EN1993-1-5 §5.1"),
        ),
        risultato=taglio_instab.hw_t, unita="-", clausola="EN1993-1-1 §6.2.6(6)/EN1993-1-5 §5.1(2)",
        esito="soddisfatta" if not taglio_instab.richiede_verifica else "non soddisfatta",
        nota="Non è una verifica di sicurezza: stabilisce se la verifica di instabilità a taglio "
             "dell'anima è richiesta. 'soddisfatta' = anima non snella (nessuna verifica necessaria); "
             "'non soddisfatta' = anima snella, verifica di instabilità a taglio richiesta (svolta comunque sotto).",
    )


def _passo_vb_rd(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    materiali = output.materiali
    hw_mm = inputs.h_mm - 2.0 * inputs.tf_mm
    eps = epsilon(materiali.fyk_MPa)
    et = eta(materiali.fyk_MPa)
    coeff_cw = calcola_cw(lambda_w(hw_mm, inputs.tw_mm, eps))
    vbw = vbw_rd_kN(coeff_cw, materiali.fyd_MPa, hw_mm, inputs.tw_mm, materiali.gamma_m1)
    vbw_max = vbw_rd_max_kN(et, materiali.fyd_MPa, hw_mm, inputs.tw_mm, materiali.gamma_m1)
    larghezza_eff = larghezza_efficace_ala_mm(inputs.b_mm, eps, inputs.tf_mm)
    c_flangia = fattore_c67_flangia(inputs.ly_mm, larghezza_eff, inputs.tf_mm, inputs.tw_mm, hw_mm)
    mfk = momento_resistente_ali_kNm(inputs.b_mm, inputs.tf_mm, inputs.h_mm, materiali.fyd_MPa)
    rf = fattore_riduzione_ali(inputs.nsd_kN, inputs.b_mm, inputs.tf_mm, materiali.fyd_MPa, materiali.gamma_m0)
    mf_rd = rf * mfk / materiali.gamma_m0
    vbf = vbf_rd_kN(inputs.b_mm, inputs.tf_mm, materiali.fyd_MPa, c_flangia, materiali.gamma_m1, inputs.my_sd_kNm, mf_rd)
    taglio_instab = output.taglio_instabilita
    return Passo(
        simbolo="V_b,Rd",
        formula="min(V_bw,Rd + V_bf,Rd, V_bw,Rd,max) >= V_Ed,w",
        valori=(
            Valore(simbolo="V_bw,Rd", valore=vbw, unita="kN", descrizione=f"contributo dell'anima (χ_w=c_w={coeff_cw:.4g}, calcolato sopra), EN1993-1-5 eq. (5.2)"),
            Valore(simbolo="V_bf,Rd", valore=vbf, unita="kN", descrizione="contributo delle ali, EN1993-1-5 §5.4(1) eq. (5.8)"),
            Valore(simbolo="V_bw,Rd,max", valore=vbw_max, unita="kN", descrizione="valore limite superiore, EN1993-1-5 eq. (5.2) nota"),
            Valore(simbolo="V_Ed,w", valore=inputs.vy_sd_kN, unita="kN", descrizione="taglio di progetto nel piano dell'anima (v. relazione_taglio.py)"),
        ),
        risultato=taglio_instab.vb_rd_kN, unita="kN", clausola="EN1993-1-5 §5.2(1)/§5.4(1)",
        esito="soddisfatta" if taglio_instab.verifica.passed else "non soddisfatta",
        nota=f"h_w/t_w={taglio_instab.hw_t:.4g} confrontato sopra con la soglia; qui la verifica è "
             f"{'richiesta' if taglio_instab.richiede_verifica else 'non richiesta, ma comunque svolta'}.",
    )


def _passo_lambda_w(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    hw_mm = inputs.h_mm - 2.0 * inputs.tf_mm
    eps = epsilon(output.materiali.fyk_MPa)
    return Passo(
        simbolo="λ_w",
        formula="h_w / (86.4 * t_w * ε)",
        valori=(
            Valore(simbolo="h_w", valore=hw_mm, unita="mm", descrizione="altezza dell'anima, h−2t_f"),
            Valore(simbolo="t_w", valore=inputs.tw_mm, unita="mm"),
            Valore(simbolo="ε", valore=eps, descrizione="ε=sqrt(235/f_yk), calcolato con f_yk"),
        ),
        risultato=lambda_w(hw_mm, inputs.tw_mm, eps), unita="-",
        clausola="EN1993-1-5 §5.3(3) eq. (5.5)-like, k_τ=5,34 (pannello non irrigidito, incorporato nella costante 86,4)",
        nota="Snellezza dell'anima a taglio: alimenta χ_w=c_w sotto, componente anima di V_b,Rd.",
    )


def _passo_chi_w(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    hw_mm = inputs.h_mm - 2.0 * inputs.tf_mm
    eps = epsilon(output.materiali.fyk_MPa)
    lam_w = lambda_w(hw_mm, inputs.tw_mm, eps)
    return Passo(
        simbolo="χ_w",
        formula="0.83 / λ_w",
        valori=(Valore(simbolo="λ_w", valore=lam_w, descrizione="calcolato sopra"),),
        risultato=calcola_cw(lam_w), unita="-",
        clausola="EN1993-1-5 Tab. 5.1 (solo il ramo 0,83/λ̄_w ≤ 1,08, non irrigidito — v. docstring del modulo)",
        nota="Fattore di riduzione per instabilità a taglio dell'anima (c_w nel codice), componente V_bw,Rd.",
    )
