"""Unit tests for the Tool 2 physics (NTC2018 §6.5.3.1.2, rows 54-61/85-88), Tratto A STR_1/SISMA.1."""
import math

import pytest

from strutture.members.muro.ribaltamento_scorrimento import (
    fattore_sicurezza_ribaltamento,
    fattore_sicurezza_scorrimento,
    forze_normale_tangente_base,
    momento_ribaltante,
    momento_stabilizzante,
    risultante_orizzontale,
    risultante_verticale,
    spinte_orizzontali_verticali,
)

pytestmark = pytest.mark.unit


def test_str1_full_chain_matches_row56():
    forze = spinte_orizzontali_verticali(ka=0.324159, delta_d_rad=0.0, dq_kN_m2=3.0, h_tot_m=2.7, gamma_g_terr=1.3, gamma_terr_kN_m3=19.7)
    assert forze.sh_q_kN == pytest.approx(2.62569, rel=1e-5)
    assert forze.sh_terr_kN == pytest.approx(30.2597, rel=1e-5)
    assert forze.sv_q_kN == pytest.approx(0.0)
    assert forze.sv_terr_kN == pytest.approx(0.0)

    m_rib = momento_ribaltante(sh_q_kN=forze.sh_q_kN, sh_terr_kN=forze.sh_terr_kN, h_tot_m=2.7, braccio_terr_m=2.7 / 3)
    assert m_rib == pytest.approx(30.7784, rel=1e-5)

    m_stab = momento_stabilizzante(sv_q_kN=0.0, sv_terr_kN=0.0, x_sv_m=1.325, m_terr_kNm=93.6558, m_muro_kNm=31.3462)
    assert m_stab == pytest.approx(125.002, rel=1e-5)

    n_tot = risultante_verticale(w_muro_kN=47.385, w_terr_kN=70.6836, sv_q_kN=0.0, sv_terr_kN=0.0)
    assert n_tot == pytest.approx(118.0686, rel=1e-5)
    r_tot = risultante_orizzontale(sh_q_kN=forze.sh_q_kN, sh_terr_kN=forze.sh_terr_kN)
    assert r_tot == pytest.approx(32.8854, rel=1e-5)

    assert fattore_sicurezza_ribaltamento(m_stab_kNm=m_stab, m_rib_kNm=m_rib) == pytest.approx(4.06135, rel=1e-5)
    phi_d = math.radians(30.69)
    assert fattore_sicurezza_scorrimento(phi_d_rad=phi_d, n_tot_kN=n_tot, r_tot_kN=r_tot, omega_rad=0.0) == pytest.approx(2.13092, rel=1e-5)


def test_fattore_sicurezza_scorrimento_nonzero_omega_uses_both_terms():
    """ω≠0 exercises the sheet's full numerator/denominator (not just the ω=0 shortcut)."""
    phi_d, n_tot, r_tot, omega = math.radians(30), 100.0, 30.0, math.radians(10)
    atteso = math.tan(phi_d) * (n_tot * math.cos(omega) + r_tot * math.sin(omega)) / (-n_tot * math.sin(omega) + r_tot * math.cos(omega))
    assert fattore_sicurezza_scorrimento(phi_d_rad=phi_d, n_tot_kN=n_tot, r_tot_kN=r_tot, omega_rad=omega) == pytest.approx(atteso)


def test_forze_normale_tangente_base_omega_zero_is_identity():
    """A base orizzontale (omega=0) la normale/tangente coincidono con Ntot/Rtot."""
    normale, tangente = forze_normale_tangente_base(n_tot_kN=100.0, r_tot_kN=30.0, omega_rad=0.0)
    assert normale == pytest.approx(100.0)
    assert tangente == pytest.approx(30.0)


def test_forze_normale_tangente_base_matches_scorrimento_geometry():
    """Stessa scomposizione geometrica gia' usata (e collaudata) dal denominatore/numeratore di
    `fattore_sicurezza_scorrimento` per lo stesso omega: la funzione estratta deve riprodurla
    esattamente, cosi' la capacita' portante puo' riusarla per H/V sulla base inclinata (HIGH
    finding: prima non venivano scomposti affatto)."""
    n_tot, r_tot, omega = 100.0, 30.0, math.radians(10)
    normale, tangente = forze_normale_tangente_base(n_tot_kN=n_tot, r_tot_kN=r_tot, omega_rad=omega)
    assert normale == pytest.approx(n_tot * math.cos(omega) + r_tot * math.sin(omega))
    assert tangente == pytest.approx(-n_tot * math.sin(omega) + r_tot * math.cos(omega))
    phi_d = math.radians(28.0)
    atteso_os = math.tan(phi_d) * normale / tangente
    assert fattore_sicurezza_scorrimento(phi_d_rad=phi_d, n_tot_kN=n_tot, r_tot_kN=r_tot, omega_rad=omega) == pytest.approx(atteso_os)


def test_spinte_seismic_factor_scales_all_terms():
    base = spinte_orizzontali_verticali(ka=0.4, delta_d_rad=0.2, dq_kN_m2=1.2, h_tot_m=2.7, gamma_g_terr=1.0, gamma_terr_kN_m3=19.7)
    scaled = spinte_orizzontali_verticali(
        ka=0.4, delta_d_rad=0.2, dq_kN_m2=1.2, h_tot_m=2.7, gamma_g_terr=1.0, gamma_terr_kN_m3=19.7, fattore_sismico=1.5
    )
    assert scaled.sh_q_kN == pytest.approx(base.sh_q_kN * 1.5)
    assert scaled.sh_terr_kN == pytest.approx(base.sh_terr_kN * 1.5)
    assert scaled.sv_q_kN == pytest.approx(base.sv_q_kN * 1.5)
    assert scaled.sv_terr_kN == pytest.approx(base.sv_terr_kN * 1.5)
