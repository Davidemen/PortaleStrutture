"""Verified restatement (docs/architecture-phase2.md) of `taglio_slu.py` (Tool 3, NTC2018
§4.1.2.3.5.2, traliccio a inclinazione variabile — cot θ, V_Rcd, V_Rsd) and `capacity_design.py`
(Tool 6, NTC2018 §7.4.4.1.1 — taglio di gerarchia delle resistenze V_Ed,max). `z` (braccio di leva
interno, `ArmaturaLimitiOutput.z_mm`) and the material design strengths are cited directly from
the output they were already computed into, exactly as the architecture brief allows for a value
the calling `Traccia` does not itself need to re-derive.

Notation identifiers must be grammar-legal: `strutture.shared.relazione.notazione` tokens cannot
contain whitespace, so the UI symbol hint "cotg θ" (`TaglioOutput.cotg_theta`) is only ever used
as a `Passo.simbolo` (free text, never parsed) — the identifier used inside later formulas is
"cotgθ" (no space, still the same value).
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .capacity_design import GAMMA_RD_CAPACITY
from .models import ClasseDuttilita, TraveRettangolareInput, TraveRettangolareOutput
from .taglio_slu import COTG_THETA_MAX, COTG_THETA_MIN, RIDUZIONE_RESISTENZA_CLS

MM2_PER_M_A_MM2_PER_MM = 1000.0  # shared.units.mm2_per_m_to_mm2_per_mm


def traccia_taglio(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Traccia:
    """4 passi: cotg θ, V_Rcd, V_Rsd, V_Rd (Check "Resistenza a taglio")."""
    return Traccia(
        titolo="Resistenza a taglio",
        passi=(_passo_cotg_theta(inputs, output), _passo_vrdc(inputs, output), _passo_vrds(inputs, output), _passo_vrd(inputs, output)),
    )


def traccia_capacity_design(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Traccia:
    """1 passo: V_Ed,max (Check "Capacity design a taglio", NTC2018 §7.4.4.1.1)."""
    return Traccia(titolo="Capacity design a taglio", passi=(_passo_ved_max(inputs, output),))


def _sin2_theta_formula() -> str:
    return f"(A_sw / {MM2_PER_M_A_MM2_PER_MM:g}) * f_yd / (b * {RIDUZIONE_RESISTENZA_CLS:g} * f_cd)"


def _valori_taglio_base(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> tuple[Valore, ...]:
    materiali = output.materiali
    return (
        Valore(simbolo="A_sw", valore=output.armatura.asw_per_m_mm2, unita="mm²/m", descrizione="armatura a taglio presente"),
        Valore(simbolo="f_yd", valore=materiali.acciaio.fyd_MPa, unita="MPa"),
        Valore(simbolo="b", valore=inputs.b_mm, unita="mm"),
        Valore(simbolo="f_cd", valore=materiali.calcestruzzo.fcd_MPa, unita="MPa"),
    )


def _passo_cotg_theta(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    sin2_theta = _sin2_theta_formula()
    return Passo(
        simbolo="cotg θ",
        formula=f"min(max(sqrt((1 - {sin2_theta}) / ({sin2_theta})), {COTG_THETA_MIN:g}), {COTG_THETA_MAX:g})",
        valori=_valori_taglio_base(inputs, output),
        risultato=output.taglio.cotg_theta, unita="-", clausola="NTC2018 §4.1.2.3.5.2",
        nota=f"Cotangente dell'inclinazione dei puntoni di calcestruzzo, limitata all'intervallo [{COTG_THETA_MIN:g}; {COTG_THETA_MAX:g}].",
    )


def _passo_vrdc(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    return Passo(
        simbolo="V_Rcd",
        formula=f"z * b * {RIDUZIONE_RESISTENZA_CLS:g} * f_cd * (cos(α) / sin(α) + cotgθ) / (1 + cotgθ^2)",
        valori=(
            Valore(simbolo="z", valore=output.armatura.z_mm, unita="mm", descrizione="braccio di leva interno, z=0,9·d"),
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm"),
            Valore(simbolo="f_cd", valore=output.materiali.calcestruzzo.fcd_MPa, unita="MPa"),
            Valore(simbolo="α", valore=inputs.alpha_staffe_deg, unita="°", descrizione="inclinazione delle staffe rispetto all'asse della trave"),
            Valore(simbolo="cotgθ", valore=output.taglio.cotg_theta, descrizione="cotangente dell'inclinazione dei puntoni, calcolata sopra"),
        ),
        risultato=output.taglio.vrdc_kN, unita="kN", scala=1e-3, clausola="NTC2018 §4.1.2.3.5.2",
        nota="Resistenza a taglio lato calcestruzzo (compressione dei puntoni).",
    )


def _passo_vrds(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    return Passo(
        simbolo="V_Rsd",
        formula=f"z * (A_sw / {MM2_PER_M_A_MM2_PER_MM:g}) * f_yd * (cos(α) / sin(α) + cotgθ) * sin(α)",
        valori=(
            Valore(simbolo="z", valore=output.armatura.z_mm, unita="mm"),
            Valore(simbolo="A_sw", valore=output.armatura.asw_per_m_mm2, unita="mm²/m"),
            Valore(simbolo="f_yd", valore=output.materiali.acciaio.fyd_MPa, unita="MPa"),
            Valore(simbolo="α", valore=inputs.alpha_staffe_deg, unita="°"),
            Valore(simbolo="cotgθ", valore=output.taglio.cotg_theta),
        ),
        risultato=output.taglio.vrds_kN, unita="kN", scala=1e-3, clausola="NTC2018 §4.1.2.3.5.2",
        nota="Resistenza a taglio lato armatura (snervamento delle staffe).",
    )


def _passo_vrd(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    taglio = output.taglio
    soddisfatta = taglio.vrd_kN >= inputs.ved_kN
    return Passo(
        simbolo="V_Rd",
        formula="min(V_Rcd, V_Rsd) >= V_Ed",
        valori=(
            Valore(simbolo="V_Rcd", valore=taglio.vrdc_kN, unita="kN"),
            Valore(simbolo="V_Rsd", valore=taglio.vrds_kN, unita="kN"),
            Valore(simbolo="V_Ed", valore=inputs.ved_kN, unita="kN", descrizione="taglio di calcolo allo SLU"),
        ),
        risultato=taglio.vrd_kN, unita="kN", clausola="NTC2018 §4.1.2.3.5.2",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Resistenza a taglio di progetto, minimo fra lato calcestruzzo e lato armatura.",
    )


def _passo_ved_max(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    """Review finding (WRONG_FORMULA + MISLEADING): NTC2018 §7.4.4.1.1's full capacity-design shear
    demand also SUMS the shear from gravity loads on the beam taken as simply supported in the
    seismic combination (a term always additive, never available as an input of this tool); the
    quantity restated here is only the moment-based contribution, so it is named `V_Ed,M` (never
    `V_Ed,max`, which would claim completeness) and γ_Rd is exposed as its own `Valore` instead of
    being folded into a numeric literal coefficient."""
    dettagli, mrd_kNm = output.dettagli_costruttivi, output.flessione.mrd_kNm
    classe: ClasseDuttilita = inputs.classe_duttilita
    gamma_rd = GAMMA_RD_CAPACITY[classe]
    soddisfatta = dettagli.ved_max_kN <= output.taglio.vrd_kN
    return Passo(
        simbolo="V_Ed,M",
        formula="γ_Rd * (M_Rd + M_Rd) * min(1, M_Rc / M_Rd) / L_t <= V_Rd",
        valori=(
            Valore(simbolo="γ_Rd", valore=gamma_rd, descrizione=f"fattore di sovraresistenza NTC2018 §7.4.4.1.1 per {classe}"),
            Valore(simbolo="M_Rd", valore=mrd_kNm, unita="kNm", descrizione="momento resistente della trave a entrambe le estremità (pari a MRb)"),
            Valore(simbolo="M_Rc", valore=inputs.mrc_kNm, unita="kNm", descrizione="momento resistente del pilastro convergente nel nodo"),
            Valore(simbolo="L_t", valore=inputs.lt_m, unita="m", descrizione="luce della trave"),
            Valore(simbolo="V_Rd", valore=output.taglio.vrd_kN, unita="kN"),
        ),
        risultato=dettagli.ved_max_kN, unita="kN", clausola="NTC2018 §7.4.4.1.1",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Solo il contributo dei momenti resistenti di estremità: la domanda di gerarchia delle "
             "resistenze completa richiede di sommarvi il taglio da carichi gravitazionali sulla trave "
             "appoggiata-appoggiata nella combinazione sismica (NTC2018 §7.4.4.1.1), non calcolato da "
             "questo strumento e quindi non incluso nel confronto con V_Rd sopra.",
    )
