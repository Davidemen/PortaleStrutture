"""Assembles Tool 1 (`SpintaCombo`) for one combination — split out of `tool.py`, regola dura 12
dei moduli piccoli.
"""
import math

from strutture.shared.divergences import legacy

from .angoli_progetto import delta_d_rad, phi_d_rad
from .combinazioni import SEISMIC_COMBOS, fattori_combo
from .coulomb import ka_coulomb
from .models import GeometriaResult, MuroSostegnoInput, NomeCombo, SpintaCombo
from .mononobe_okabe import coefficienti_sismici, kae_mononobe_okabe
from .pesi import pesi_combo


def _parametri_sismici_spinta(nome: NomeCombo, *, inputs: MuroSostegnoInput, phi_d: float, delta_d: float, beta_rad: float, psi_rad: float, s_sismico: float):
    """kh/kv/theta/ka/kv_factor for a seismic combination (Mononobe-Okabe + EN1998-5 §7.3.2.2(2)P
    vertical-coefficient scaling of the monolith's own weight)."""
    segno_kv = 1.0 if nome == "SISMA_1" else -1.0
    kh, kv, theta_rad = coefficienti_sismici(s=s_sismico, ag_g=inputs.ag_g, beta_m=inputs.beta_m, segno_kv=segno_kv)
    kv_factor = 1.0
    if not legacy("muro-sostegno/inerzia-sismica-muro-terreno-assente", inputs.legacy_compat):
        kv_factor = 1 + kv
    ka = kae_mononobe_okabe(phi_d_rad=phi_d, delta_d_rad=delta_d, beta_rad=beta_rad, psi_rad=psi_rad, theta_rad=theta_rad)
    return kh, kv, theta_rad, ka, kv_factor


def spinta_combo(nome: NomeCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult, s_sismico: float) -> SpintaCombo:
    fattori = fattori_combo(nome, legacy_compat=inputs.legacy_compat)
    phi_d = phi_d_rad(inputs.phi_deg, fattori.gamma_phi_terr, legacy_compat=inputs.legacy_compat)
    delta_d = delta_d_rad(inputs.delta_deg, fattori.gamma_phi_terr, legacy_compat=inputs.legacy_compat)
    beta_rad, psi_rad = math.radians(inputs.beta_deg), math.radians(inputs.psi_deg)
    sismica = nome in SEISMIC_COMBOS
    kh = kv = theta_rad = None
    kv_factor = 1.0
    if sismica:
        kh, kv, theta_rad, ka, kv_factor = _parametri_sismici_spinta(
            nome, inputs=inputs, phi_d=phi_d, delta_d=delta_d, beta_rad=beta_rad, psi_rad=psi_rad, s_sismico=s_sismico
        )
    else:
        ka = ka_coulomb(phi_d_rad=phi_d, delta_d_rad=delta_d, beta_rad=beta_rad, psi_rad=psi_rad)
    pesi = pesi_combo(
        gamma_cls_kN_m3=inputs.gamma_cls_kN_m3,
        gamma_terr_sat_kN_m3=inputs.gamma_terr_sat_kN_m3,
        geometria=geometria,
        gamma_g_muro=fattori.gamma_g_muro,
        gamma_g_terr=fattori.gamma_g_terr,
        kv_factor=kv_factor,
    )
    return SpintaCombo(
        nome=nome,
        sismica=sismica,
        gamma_g_muro=fattori.gamma_g_muro,
        gamma_phi_terr=fattori.gamma_phi_terr,
        gamma_g_terr=fattori.gamma_g_terr,
        gamma_q=fattori.gamma_q,
        phi_d_rad=phi_d,
        delta_d_rad=delta_d,
        w_muro_kN=pesi.w_muro_kN,
        m_muro_kNm=pesi.m_muro_kNm,
        w_terr_kN=pesi.w_terr_kN,
        m_terr_kNm=pesi.m_terr_kNm,
        ka=ka,
        kh=kh,
        kv=kv,
        theta_rad=theta_rad,
    )
