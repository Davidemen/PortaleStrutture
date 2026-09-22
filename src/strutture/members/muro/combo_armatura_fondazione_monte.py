"""Tool 6 (`armatura-fondazione-monte`) per-combination bending + governing-combination assembly
— split out of `tool.py`, regola dura 12 dei moduli piccoli.
"""
from . import armatura_fondazione_monte as fond_monte
from . import armatura_minima, rebar_selection
from .armatura_comune import armatura_minima_cm2_m
from .models import (
    ArmaturaFondazioneMonteCombo,
    ArmaturaFondazioneMonteResult,
    GeometriaResult,
    MuroSostegnoInput,
    PressioniCombo,
    RibaltamentoScorrimentoCombo,
    SpintaCombo,
)


def _armatura_fondazione_monte_combo(
    spinta: SpintaCombo,
    verifica: RibaltamentoScorrimentoCombo,
    pressioni: PressioniCombo,
    *,
    inputs: MuroSostegnoInput,
    geometria: GeometriaResult,
    fyd_MPa: float,
) -> ArmaturaFondazioneMonteCombo:
    p_star_star_kPa = fond_monte.pressione_interpolata_kPa(
        b_star_m=pressioni.b_star_m, p_valle_kPa=pressioni.p_valle_kPa, p_monte_kPa=pressioni.p_monte_kPa, b_fond_m=geometria.b_fond_m, b_monte_m=inputs.b_monte_m
    )
    m_ed_p_kNm = fond_monte.momento_pressione_kNm(
        p_monte_kPa=pressioni.p_monte_kPa, p_star_star_kPa=p_star_star_kPa, b_monte_m=inputs.b_monte_m, b_fond_m=geometria.b_fond_m, b_star_m=pressioni.b_star_m
    )
    m_ed_terr_kNm = fond_monte.momento_terreno_kNm(w_terr_kN=spinta.w_terr_kN, b_monte_m=inputs.b_monte_m, b_fond_m=geometria.b_fond_m, x_terr_m=geometria.x_terr_m)
    sv_tot_kN = verifica.sv_q_kN + verifica.sv_terr_kN
    m_ed_sv_kNm = fond_monte.momento_sovraccarico_verticale_kNm(
        sv_tot_kN=sv_tot_kN, x_sv_m=geometria.x_sv_m, b_fond_m=geometria.b_fond_m, b_monte_m=inputs.b_monte_m
    )
    m_ed_fond_kNm = fond_monte.momento_autopeso_kNm(
        b_monte_m=inputs.b_monte_m, gamma_g_muro=spinta.gamma_g_muro, gamma_cls_kN_m3=inputs.gamma_cls_kN_m3,
        s_fond_m=inputs.s_fond_m, legacy_compat=inputs.legacy_compat,
    )
    m_ed_tot_kNm = m_ed_terr_kNm + m_ed_sv_kNm + m_ed_fond_kNm + m_ed_p_kNm
    d_m = inputs.s_fond_m - inputs.copertura_fondazione_m
    as_nec_cm2_m = rebar_selection.as_necessaria_cm2_m(m_ed_kNm=m_ed_tot_kNm, d_m=d_m, fyd_MPa=fyd_MPa)
    return ArmaturaFondazioneMonteCombo(
        nome=spinta.nome,
        p_star_star_kPa=p_star_star_kPa,
        m_ed_p_kNm=m_ed_p_kNm,
        m_ed_terr_kNm=m_ed_terr_kNm,
        m_ed_sv_kNm=m_ed_sv_kNm,
        m_ed_fond_kNm=m_ed_fond_kNm,
        m_ed_tot_kNm=m_ed_tot_kNm,
        as_nec_cm2_m=as_nec_cm2_m,
    )


def run_armatura_fondazione_monte(
    spinte: tuple[SpintaCombo, ...],
    ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...],
    pressioni_terreno: tuple[PressioniCombo, ...],
    *,
    inputs: MuroSostegnoInput,
    geometria: GeometriaResult,
    fyd_MPa: float,
) -> ArmaturaFondazioneMonteResult:
    combinazioni = tuple(
        _armatura_fondazione_monte_combo(spinta, verifica, pressioni, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa)
        for spinta, verifica, pressioni in zip(spinte, ribaltamento_scorrimento, pressioni_terreno, strict=True)
    )
    governante = max(combinazioni, key=lambda c: c.as_nec_cm2_m)
    as_nec_governante_cm2_m = rebar_selection.governante_cm2_m(tuple(c.as_nec_cm2_m for c in combinazioni))
    as_min_cm2_m = armatura_minima_cm2_m(inputs, inputs.s_fond_m - inputs.copertura_fondazione_m)
    as_progetto_cm2_m = armatura_minima.as_progetto_cm2_m(as_nec_governante_cm2_m, as_min_cm2_m, legacy_compat=inputs.legacy_compat)
    passo_m = inputs.passo_arm_fondazione_m
    return ArmaturaFondazioneMonteResult(
        combinazioni=combinazioni,
        as_nec_cm2_m=as_nec_governante_cm2_m,
        as_min_cm2_m=as_min_cm2_m,
        as_progetto_cm2_m=as_progetto_cm2_m,
        combo_governante=governante.nome,
        diametro_mm=rebar_selection.diametro_mm(as_progetto_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
        passo_m=passo_m,
        callout=rebar_selection.callout(as_progetto_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
    )
