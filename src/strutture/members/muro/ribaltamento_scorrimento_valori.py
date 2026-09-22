"""Numeric values behind Tool 2 (ribaltamento/scorrimento) for one combination, before the two
`Check`s and the frozen result model are built — split out of `verifica_ribaltamento_scorrimento.py`,
regola dura 12 dei moduli piccoli.
"""
import math
from typing import NamedTuple

from strutture.shared.divergences import legacy
from strutture.shared.ntc_combos import fattori_resistenza

from .angoli_progetto import phi_d_rad
from .models import GeometriaResult, MuroSostegnoInput, SpintaCombo
from .ribaltamento_scorrimento import (
    GAMMA_R_RIBALTAMENTO_R3,
    fattore_sicurezza_ribaltamento,
    fattore_sicurezza_scorrimento,
    momento_ribaltante,
    momento_stabilizzante,
    risultante_orizzontale,
    risultante_verticale,
    soglia_verifica,
    spinte_orizzontali_verticali,
)


def _phi_scorrimento_rad(inputs: MuroSostegnoInput, spinta: SpintaCombo) -> float:
    """Design friction angle for sliding on the base (NTC2018 §6.5.3.1.1 / EN1997-1 §6.5.3): the
    FOUNDATION soil's, with this combination's own γφ, when the 'Terreno di fondazione' block is
    filled in drained condition; otherwise (no block, undrained block, Excel mode) the backfill's
    angle, the only one the sheet knows — proof-read finding: with a weaker foundation soil the
    sliding resistance was overstated by tan(φ_d,rinterro)/tan(φ_d,fond)."""
    if inputs.legacy_compat or inputs.terreno_condizione != "drenata" or inputs.terreno_phi_k_deg is None:
        return spinta.phi_d_rad
    return phi_d_rad(inputs.terreno_phi_k_deg, spinta.gamma_phi_terr)


def _forza_inerzia_orizzontale(spinta: SpintaCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult) -> tuple[float, float]:
    """EN1998-5 §7.3.2.2(2)P / NTC2018 §7.11.6.2.1: horizontal inertia force of the wall+backfill
    monolith (kh already scales the seismic thrust via Mononobe-Okabe; it must also scale the
    monolith's own mass, on top of MSTAB/Ntot already carrying the (1±kv) weight from `pesi_combo`)."""
    if not spinta.sismica or legacy("muro-sostegno/inerzia-sismica-muro-terreno-assente", inputs.legacy_compat):
        return 0.0, 0.0
    fh_kN = spinta.kh * (spinta.w_muro_kN + spinta.w_terr_kN)
    m_fh_kNm = spinta.kh * (spinta.w_muro_kN * geometria.z_muro_m + spinta.w_terr_kN * geometria.z_terr_m)
    return fh_kN, m_fh_kNm


class ValoriRibaltamentoScorrimento(NamedTuple):
    """Intermediate numeric results for one combination."""

    dq_kN_m2: float
    sh_q_kN: float
    sh_terr_kN: float
    sv_q_kN: float
    sv_terr_kN: float
    braccio_terr_m: float
    fh_kN: float
    m_fh_kNm: float
    m_rib_kNm: float
    m_stab_kNm: float
    n_tot_kN: float
    r_tot_kN: float
    or_ribaltamento: float
    phi_scorrimento_rad: float
    os_scorrimento: float
    soglia_rib: float
    soglia_scorr: float


def _forze_e_braccio(spinta: SpintaCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult):
    dq_kN_m2 = inputs.q_kN_m2 * spinta.gamma_q
    fattore_sismico = (1 + spinta.kv) * inputs.gamma_e if spinta.sismica else 1.0
    braccio_terr_m = geometria.h_muro_tot_m / 2 if spinta.sismica else geometria.h_muro_tot_m / 3
    forze = spinte_orizzontali_verticali(
        ka=spinta.ka,
        delta_d_rad=spinta.delta_d_rad,
        dq_kN_m2=dq_kN_m2,
        h_tot_m=geometria.h_muro_tot_m,
        gamma_g_terr=spinta.gamma_g_terr,
        gamma_terr_kN_m3=inputs.gamma_terr_sat_kN_m3,
        fattore_sismico=fattore_sismico,
    )
    fh_kN, m_fh_kNm = _forza_inerzia_orizzontale(spinta, inputs=inputs, geometria=geometria)
    return dq_kN_m2, forze, braccio_terr_m, fh_kN, m_fh_kNm


def valori_ribaltamento_scorrimento(spinta: SpintaCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult) -> ValoriRibaltamentoScorrimento:
    dq_kN_m2, forze, braccio_terr_m, fh_kN, m_fh_kNm = _forze_e_braccio(spinta, inputs=inputs, geometria=geometria)
    m_rib_kNm = momento_ribaltante(
        sh_q_kN=forze.sh_q_kN, sh_terr_kN=forze.sh_terr_kN, h_tot_m=geometria.h_muro_tot_m, braccio_terr_m=braccio_terr_m, m_fh_kNm=m_fh_kNm
    )
    m_stab_kNm = momento_stabilizzante(
        sv_q_kN=forze.sv_q_kN, sv_terr_kN=forze.sv_terr_kN, x_sv_m=geometria.x_sv_m, m_terr_kNm=spinta.m_terr_kNm, m_muro_kNm=spinta.m_muro_kNm
    )
    n_tot_kN = risultante_verticale(w_muro_kN=spinta.w_muro_kN, w_terr_kN=spinta.w_terr_kN, sv_q_kN=forze.sv_q_kN, sv_terr_kN=forze.sv_terr_kN)
    r_tot_kN = risultante_orizzontale(sh_q_kN=forze.sh_q_kN, sh_terr_kN=forze.sh_terr_kN, fh_kN=fh_kN)
    or_ribaltamento = fattore_sicurezza_ribaltamento(m_stab_kNm=m_stab_kNm, m_rib_kNm=m_rib_kNm)
    phi_scorrimento = _phi_scorrimento_rad(inputs, spinta)
    os_scorrimento = fattore_sicurezza_scorrimento(
        phi_d_rad=phi_scorrimento, n_tot_kN=n_tot_kN, r_tot_kN=r_tot_kN, omega_rad=math.radians(inputs.omega_deg)
    )
    # NTC2018 Tab. 6.5.I γR (Approccio 2, A1+M1+R3 per le opere di sostegno, §6.5.3.1.1): the sheet
    # (`legacy_compat=True`) never divides the resistance by γR, i.e. it checks OR/OS >= 1.
    soglia_rib = soglia_verifica(sismica=spinta.sismica, legacy_compat=inputs.legacy_compat, gamma_r_statico=GAMMA_R_RIBALTAMENTO_R3)
    soglia_scorr = soglia_verifica(sismica=spinta.sismica, legacy_compat=inputs.legacy_compat, gamma_r_statico=fattori_resistenza("scorrimento").r3)
    return ValoriRibaltamentoScorrimento(
        dq_kN_m2=dq_kN_m2,
        sh_q_kN=forze.sh_q_kN,
        sh_terr_kN=forze.sh_terr_kN,
        sv_q_kN=forze.sv_q_kN,
        sv_terr_kN=forze.sv_terr_kN,
        braccio_terr_m=braccio_terr_m,
        fh_kN=fh_kN,
        m_fh_kNm=m_fh_kNm,
        m_rib_kNm=m_rib_kNm,
        m_stab_kNm=m_stab_kNm,
        n_tot_kN=n_tot_kN,
        r_tot_kN=r_tot_kN,
        or_ribaltamento=or_ribaltamento,
        phi_scorrimento_rad=phi_scorrimento,
        os_scorrimento=os_scorrimento,
        soglia_rib=soglia_rib,
        soglia_scorr=soglia_scorr,
    )
