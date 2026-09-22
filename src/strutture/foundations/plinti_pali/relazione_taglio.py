"""Verified restatement (docs/architecture-phase2.md §6) of Tool-4's one-way shear check
(`taglio_punzonamento.py::taglio`, EC2 §6.2.2), STANDARD mode only: `k` clamped at 2 (`k_size`),
`av` clamped to `[0,5d;2d]` before the reduction, EC2 eq. 6.5's companion crushing check computed.

`d_v` (this Traccia's own effective-depth estimate, EC2 §6.2.2's coarser `2·⌀` margin) is a
DIFFERENT value from `d_X`/`d_Y` of `relazione_flessione.py` (its own `1,5·⌀` margin) — the package
computes shear/punching geometry independently of the flexural design, so the symbol is kept
distinct (`d_v`, never bare `d`) rather than implying the two coincide. `N_tot`/`W` are cited from
`output.inviluppo`/"calcolato sopra" (Traccia "Reazioni sui pali"), never re-derived."""
from strutture.shared.ec2_shear.v_min import V_MIN_COEFFICIENT_EN
from strutture.shared.ec2_shear.v_rd_c import C_RD_C_COEFFICIENT_EN, RHO_L_MAX
from strutture.shared.relazione import Passo, Traccia, Valore

from .input import PlintoSuPaliInput
from .models import PlintoSuPaliOutput
from .models_taglio import Taglio
from .relazione_comune import fcd_frammento, nu_vrd_max_frammento, valore_fck, valore_gamma_c
from .taglio_punzonamento import MARGIN_EFFECTIVE_DEPTH_FACTOR

EC2_TAGLIO = "EN 1992-1-1 §6.2.2"


def traccia_taglio(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput, peso_kN: float) -> Traccia:
    """6 passi: altezza utile, taglio ridotto (con la riduzione a_v), resistenza del calcestruzzo,
    Check "Taglio", Check "Schiacciamento del calcestruzzo al filo (taglio)"."""
    taglio = output.taglio
    n_tot = next(r.valore for r in output.inviluppo if r.grandezza == "n_totale_max")
    h_mm, c_mm = inputs.h_plinto_m * 1000.0, inputs.copriferro_cm * 10.0
    b_mm = inputs.ax_m * 1000.0
    passi = (
        _passo_d(h_mm, c_mm, inputs.diametro_long_assunto_mm, taglio),
        _passo_ved_ridotto(inputs, taglio, n_tot, peso_kN),
        _passo_vrd_c(inputs, output, taglio, b_mm),
        _passo_check_taglio(taglio),
        _passo_check_schiacciamento(inputs, output, taglio, n_tot, peso_kN, b_mm),
    )
    return Traccia(titolo="Resistenza a taglio a distanza ridotta a_v", passi=passi)


def _passo_d(h_mm: float, c_mm: float, diametro_long_mm: float, taglio: Taglio) -> Passo:
    return Passo(
        simbolo="d_v", formula=f"H - c - {MARGIN_EFFECTIVE_DEPTH_FACTOR:g} * φ_l",
        valori=(
            Valore(simbolo="H", valore=h_mm, unita="mm", descrizione="altezza del plinto (input in m, qui in mm)"),
            Valore(simbolo="c", valore=c_mm, unita="mm", descrizione="copriferro netto (input in cm, qui in mm)"),
            Valore(simbolo="φ_l", valore=diametro_long_mm, unita="mm", descrizione="diametro longitudinale assunto per la stima dell'altezza utile"),
        ),
        risultato=taglio.d_mm, unita="mm",
        nota="Altezza utile per taglio e punzonamento, margine convenzionale di 2 diametri (diverso da quello, 1,5 diametri, usato per la flessione).",
    )


def _passo_ved_ridotto(inputs: PlintoSuPaliInput, taglio: Taglio, n_tot: float, peso_kN: float) -> Passo:
    return Passo(
        simbolo="V_Ed'", formula="(N_tot + W) / 2 * min(max(a_v, 0.5 * d_v), 2 * d_v) / (2 * d_v)",
        valori=(
            Valore(simbolo="N_tot", valore=n_tot, unita="kN", descrizione="carico totale massimo in colonna (inviluppo)"),
            Valore(simbolo="W", valore=peso_kN, unita="kN", descrizione="peso proprio del plinto, calcolato sopra"),
            Valore(simbolo="a_v", valore=inputs.av_mm, unita="mm", descrizione="distanza ridotta di verifica, dato di ingresso"),
            Valore(simbolo="d_v", valore=taglio.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
        ),
        risultato=taglio.ved_ridotto_kN, unita="kN", clausola=f"{EC2_TAGLIO}(6)",
        nota="Taglio di calcolo ridotto sulla distanza a_v dal filo del palo (a_v limitato a [0,5·d_v; 2·d_v]); "
             "N/2 perché il carico è ripartito su due file di pali.",
    )


def _passo_vrd_c(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput, taglio: Taglio, b_mm: float) -> Passo:
    formula = (
        f"max({C_RD_C_COEFFICIENT_EN:g} / γ_c * k * (100 * min(ρ, {RHO_L_MAX:g}) * f_ck)^(1/3), "
        f"{V_MIN_COEFFICIENT_EN:g} * k^1.5 * sqrt(f_ck)) * b * d_v / 1000"
    )
    return Passo(
        simbolo="V_Rd,c", formula=formula,
        valori=(
            valore_gamma_c(inputs.gamma_c),
            Valore(simbolo="k", valore=taglio.k, descrizione="fattore dimensionale, k=min(1+√(200/d_v);2), EC2 §6.2.2(1)"),
            Valore(simbolo="ρ", valore=taglio.rho, descrizione="quota di armatura tesa disposta, ρ=A_s,prov,X/(1000·d_v), limitata al 2%"),
            valore_fck(output.materiali.calcestruzzo.fck_MPa),
            Valore(simbolo="b", valore=b_mm, unita="mm", descrizione="larghezza del plinto (input A_X in m, qui in mm)"),
            Valore(simbolo="d_v", valore=taglio.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
        ),
        risultato=taglio.vrd_c_kN, unita="kN", clausola=EC2_TAGLIO,
        nota="Resistenza a taglio del solo calcestruzzo, senza armatura trasversale (eq. 6.2.a).",
    )


def _passo_check_taglio(taglio: Taglio) -> Passo:
    return Passo(
        simbolo="V_Ed'/V_Rd,c", formula="V_Ed' <= V_Rd,c",
        valori=(
            Valore(simbolo="V_Ed'", valore=taglio.ved_ridotto_kN, unita="kN"),
            Valore(simbolo="V_Rd,c", valore=taglio.vrd_c_kN, unita="kN"),
        ),
        risultato=taglio.ved_ridotto_kN, unita="kN", clausola=EC2_TAGLIO,
        esito="soddisfatta" if taglio.ved_ridotto_kN <= taglio.vrd_c_kN else "non soddisfatta",
        nota="Verifica \"Taglio\".",
    )


def _passo_check_schiacciamento(
    inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput, taglio: Taglio, n_tot: float, peso_kN: float, b_mm: float,
) -> Passo:
    formula = f"(N_tot + W) / 2 <= k_V * {nu_vrd_max_frammento()} * {fcd_frammento()} * b * d_v / 1000"
    fck_MPa = output.materiali.calcestruzzo.fck_MPa
    ved_kN = (n_tot + peso_kN) / 2.0
    valori = (
        Valore(simbolo="N_tot", valore=n_tot, unita="kN", descrizione="carico totale massimo in colonna (inviluppo)"),
        Valore(simbolo="W", valore=peso_kN, unita="kN", descrizione="peso proprio del plinto, calcolato sopra"),
        Valore(simbolo="k_V", valore=inputs.coeff_vrd_max,
               descrizione="coefficiente del limite di schiacciamento: EN 1992-1-1 eq. 6.5 dà 0,5; qui lo strumento "
                           "riusa il coefficiente di v_Rd,max scelto in ingresso (0,4 di default, a favore di sicurezza "
                           "— registro: plinti-pali/coefficiente-vrd-max-scelta-da-confermare)"),
        valore_fck(fck_MPa), valore_gamma_c(inputs.gamma_c),
        Valore(simbolo="b", valore=b_mm, unita="mm", descrizione="larghezza del plinto, in mm"),
        Valore(simbolo="d_v", valore=taglio.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
    )
    return Passo(
        simbolo="V_Ed", formula=formula, valori=valori, risultato=ved_kN, unita="kN", clausola=f"{EC2_TAGLIO} eq. 6.5",
        esito="soddisfatta" if ved_kN <= taglio.ved_max_kN else "non soddisfatta",
        nota="Verifica \"Schiacciamento del calcestruzzo al filo (taglio)\" — schiacciamento dei puntoni di calcestruzzo "
             "al filo del palo, taglio NON ridotto da a_v.",
    )
