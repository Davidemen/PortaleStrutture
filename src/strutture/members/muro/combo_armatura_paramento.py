"""Tool 4 (`armatura-paramento`) per-combination bending + governing-combination assembly —
split out of `tool.py`, regola dura 12 dei moduli piccoli.
"""
from strutture.shared.divergences import legacy

from . import armatura_minima, rebar_selection
from . import armatura_paramento as paramento
from .armatura_comune import armatura_minima_cm2_m
from .models import (
    ArmaturaParamentoCombo,
    ArmaturaParamentoResult,
    GeometriaResult,
    MuroSostegnoInput,
    RibaltamentoScorrimentoCombo,
    SpintaCombo,
)


def _armatura_paramento_combo(
    spinta: SpintaCombo, verifica: RibaltamentoScorrimentoCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult, fyd_MPa: float
) -> ArmaturaParamentoCombo:
    if legacy("muro-sostegno/momento-paramento-altezza-piena-invece-di-stelo", inputs.legacy_compat):
        zq_m = paramento.leva_sovraccarico_m(h_muro_tot_m=geometria.h_muro_tot_m, s_fond_m=inputs.s_fond_m)
        zterr_m = paramento.leva_terreno_m(braccio_terr_m=verifica.braccio_terr_m, s_fond_m=inputs.s_fond_m)
        m_ed_kNm = paramento.momento_flettente_kNm(sh_q_kN=verifica.sh_q_kN, sh_terr_kN=verifica.sh_terr_kN, zq_m=zq_m, zterr_m=zterr_m)
    else:
        # Fixed behaviour (NTC2018 §6.5.3.1.1/§4.1.2): the stem's own thrust over its own height
        # hs = H - sfond, not Tool 2's full-height resultants reused with shifted lever arms.
        hs_m = geometria.h_muro_tot_m - inputs.s_fond_m
        fattore_sismico = (1 + spinta.kv) * inputs.gamma_e if spinta.sismica else 1.0
        forze_stelo = paramento.spinte_stelo(
            ka=spinta.ka,
            delta_d_rad=spinta.delta_d_rad,
            dq_kN_m2=verifica.dq_kN_m2,
            hs_m=hs_m,
            gamma_g_terr=spinta.gamma_g_terr,
            gamma_terr_kN_m3=inputs.gamma_terr_sat_kN_m3,
            fattore_sismico=fattore_sismico,
        )
        zq_m = paramento.leva_sovraccarico_stelo_m(hs_m=hs_m)
        zterr_m = paramento.leva_terreno_stelo_m(hs_m=hs_m)
        m_ed_kNm = paramento.momento_flettente_kNm(sh_q_kN=forze_stelo.sh_q_kN, sh_terr_kN=forze_stelo.sh_terr_kN, zq_m=zq_m, zterr_m=zterr_m)
    d_m = inputs.s_base_m - inputs.copertura_paramento_m
    as_nec_cm2_m = rebar_selection.as_necessaria_cm2_m(m_ed_kNm=m_ed_kNm, d_m=d_m, fyd_MPa=fyd_MPa)
    return ArmaturaParamentoCombo(nome=spinta.nome, zq_m=zq_m, zterr_m=zterr_m, m_ed_kNm=m_ed_kNm, as_nec_cm2_m=as_nec_cm2_m)


def run_armatura_paramento(
    spinte: tuple[SpintaCombo, ...], ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...], *, inputs: MuroSostegnoInput, geometria: GeometriaResult, fyd_MPa: float
) -> ArmaturaParamentoResult:
    combinazioni = tuple(
        _armatura_paramento_combo(spinta, verifica, inputs=inputs, geometria=geometria, fyd_MPa=fyd_MPa)
        for spinta, verifica in zip(spinte, ribaltamento_scorrimento, strict=True)
    )
    governante = max(combinazioni, key=lambda c: c.as_nec_cm2_m)
    as_nec_governante_cm2_m = rebar_selection.governante_cm2_m(tuple(c.as_nec_cm2_m for c in combinazioni))
    as_min_cm2_m = armatura_minima_cm2_m(inputs, inputs.s_base_m - inputs.copertura_paramento_m)
    as_progetto_cm2_m = armatura_minima.as_progetto_cm2_m(as_nec_governante_cm2_m, as_min_cm2_m, legacy_compat=inputs.legacy_compat)
    passo_m = inputs.passo_arm_paramento_m
    return ArmaturaParamentoResult(
        combinazioni=combinazioni,
        as_nec_cm2_m=as_nec_governante_cm2_m,
        as_min_cm2_m=as_min_cm2_m,
        as_progetto_cm2_m=as_progetto_cm2_m,
        combo_governante=governante.nome,
        diametro_mm=rebar_selection.diametro_mm(as_progetto_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
        passo_m=passo_m,
        callout=rebar_selection.callout(as_progetto_cm2_m, passo_m, legacy_compat=inputs.legacy_compat),
    )
