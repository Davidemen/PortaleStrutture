"""Assembles Tool 3 (`PressioniCombo`) for one combination — split out of `tool.py`, regola dura
12 dei moduli piccoli.
"""
from strutture.shared.report import CalcError

from .models import GeometriaResult, PressioniCombo, RibaltamentoScorrimentoCombo, SpintaCombo
from .pressioni_terreno import eccentricita_risultante, eccentricita_termine, larghezza_efficace, pressioni_valle_monte


def pressioni_combo(spinta: SpintaCombo, verifica: RibaltamentoScorrimentoCombo, *, geometria: GeometriaResult) -> PressioniCombo:
    e_muro_m, m_muro_ecc_kNm = eccentricita_termine(spinta.w_muro_kN, geometria.x_muro_m, geometria.b_fond_m)
    e_terr_m, m_terr_ecc_kNm = eccentricita_termine(spinta.w_terr_kN, geometria.x_terr_m, geometria.b_fond_m)
    sv_tot_kN = verifica.sv_q_kN + verifica.sv_terr_kN
    e_sv_m, m_sv_ecc_kNm = eccentricita_termine(sv_tot_kN, geometria.x_sv_m, geometria.b_fond_m)
    m_tot_kNm, eccentricita_m = eccentricita_risultante(
        m_rib_kNm=verifica.m_rib_kNm, m_muro_ecc_kNm=m_muro_ecc_kNm, m_terr_ecc_kNm=m_terr_ecc_kNm, m_sv_ecc_kNm=m_sv_ecc_kNm, n_tot_kN=verifica.n_tot_kN
    )
    if abs(eccentricita_m) > geometria.b_fond_m / 2:
        raise CalcError(
            f"Combinazione {spinta.nome}: eccentricità |e|={abs(eccentricita_m):.3f} m supera B/2={geometria.b_fond_m / 2:.3f} m "
            "(risultante esterna alla fondazione, verifica di pressione sul terreno non significativa)"
        )
    b_star_m = larghezza_efficace(eccentricita_m=eccentricita_m, b_fond_m=geometria.b_fond_m)
    pressioni = pressioni_valle_monte(n_tot_kN=verifica.n_tot_kN, m_tot_kNm=m_tot_kNm, b_fond_m=geometria.b_fond_m, b_star_m=b_star_m)
    return PressioniCombo(
        nome=spinta.nome,
        e_muro_m=e_muro_m,
        e_terr_m=e_terr_m,
        e_sv_m=e_sv_m,
        m_tot_kNm=m_tot_kNm,
        n_tot_kN=verifica.n_tot_kN,
        eccentricita_m=eccentricita_m,
        entro_nocciolo=b_star_m == 0,
        b_star_m=b_star_m,
        p_valle_kPa=pressioni.p_valle_kPa,
        p_monte_kPa=pressioni.p_monte_kPa,
    )
