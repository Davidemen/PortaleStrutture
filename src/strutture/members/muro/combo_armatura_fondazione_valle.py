"""Tool 5 (`armatura-fondazione-valle`) per-combination bending + governing-combination assembly
— split out of `tool.py`, regola dura 12 dei moduli piccoli.
"""
from . import armatura_fondazione_valle as fond_valle
from . import armatura_minima, rebar_selection
from .armatura_comune import armatura_minima_cm2_m
from .models import (
    ArmaturaFondazioneValleCombo,
    ArmaturaFondazioneValleResult,
    GeometriaResult,
    MuroSostegnoInput,
    PressioniCombo,
    SpintaCombo,
)


def _armatura_fondazione_valle_combo(
    spinta: SpintaCombo, pressioni: PressioniCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult, fyd_MPa: float
) -> ArmaturaFondazioneValleCombo:
    p_star_kPa = fond_valle.pressione_interpolata_kPa(
        b_star_m=pressioni.b_star_m, p_valle_kPa=pressioni.p_valle_kPa, p_monte_kPa=pressioni.p_monte_kPa, b_fond_m=geometria.b_fond_m, x_star_m=inputs.b_valle_m
    )
    m_ed_p1_kNm = fond_valle.momento_pressione_1_kNm(p_star_kPa=p_star_kPa, p_valle_kPa=pressioni.p_valle_kPa, b_valle_m=inputs.b_valle_m)
    m_ed_p2_kNm = fond_valle.momento_pressione_2_kNm(
        p_star_kPa=p_star_kPa, p_valle_kPa=pressioni.p_valle_kPa, b_star_m=pressioni.b_star_m, b_valle_m=inputs.b_valle_m
    )
    m_ed_fond_kNm = fond_valle.momento_autopeso_kNm(
        gamma_g_muro=spinta.gamma_g_muro, s_fond_m=inputs.s_fond_m, gamma_cls_kN_m3=inputs.gamma_cls_kN_m3, b_valle_m=inputs.b_valle_m
    )
    m_ed_tot_kNm = m_ed_p1_kNm + m_ed_p2_kNm + m_ed_fond_kNm
    d_m = inputs.s_fond_m - inputs.copertura_fondazione_m
    as_nec_cm2_m = rebar_selection.as_necessaria_cm2_m(m_ed_kNm=m_ed_tot_kNm, d_m=d_m, fyd_MPa=fyd_MPa)
    return ArmaturaFondazioneValleCombo(
        nome=spinta.nome,
        p_star_kPa=p_star_kPa,
        m_ed_p1_kNm=m_ed_p1_kNm,
        m_ed_p2_kNm=m_ed_p2_kNm,
        m_ed_fond_kNm=m_ed_fond_kNm,
        m_ed_tot_kNm=m_ed_tot_kNm,
        as_nec_cm2_m=as_nec_cm2_m,
    )


def run_armatura_fondazione_valle(
    spinte: tuple[SpintaCombo, ...], pressioni_terreno: tuple[PressioniCombo, ...], *, inputs: MuroSostegnoInput, geometria: GeometriaResult, fyd_MPa: float
) -> ArmaturaFondazioneValleResult:
    combinazioni = tuple(
        _armatura_fondazione_valle_combo(spinta, pressioni, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa)
        for spinta, pressioni in zip(spinte, pressioni_terreno, strict=True)
    )
    governante = max(combinazioni, key=lambda c: c.as_nec_cm2_m)
    as_nec_governante_cm2_m = rebar_selection.governante_cm2_m(tuple(c.as_nec_cm2_m for c in combinazioni))
    as_min_cm2_m = armatura_minima_cm2_m(inputs, inputs.s_fond_m - inputs.copertura_fondazione_m)
    as_progetto_cm2_m = armatura_minima.as_progetto_cm2_m(as_nec_governante_cm2_m, as_min_cm2_m, legacy_compat=inputs.legacy_compat)
    passo_m = inputs.passo_arm_fondazione_m
    return ArmaturaFondazioneValleResult(
        combinazioni=combinazioni,
        as_nec_cm2_m=as_nec_governante_cm2_m,
        as_min_cm2_m=as_min_cm2_m,
        as_progetto_cm2_m=as_progetto_cm2_m,
        combo_governante=governante.nome,
        diametro_mm=rebar_selection.diametro_mm(as_progetto_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
        passo_m=passo_m,
        callout=rebar_selection.callout(as_progetto_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
    )
