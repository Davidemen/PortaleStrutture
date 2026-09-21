"""NTC 2018 §6.4.2.1 approccio 2 (A1+M1+R3) bearing-capacity check."""
import pytest

from strutture.shared.capacita_portante.carico_limite import carico_limite_drenato
from strutture.shared.capacita_portante.verifica import (
    CITAZIONE_GAMMA_R,
    GAMMA_M_APPROCCIO_2_NTC_6_4_2_1,
    GAMMA_R_STATICO_NTC_6_4_2_1,
    verifica_drenata,
    verifica_non_drenata,
)
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit


def test_gamma_m_is_one_and_gamma_r_is_2_3_per_ntc():
    assert GAMMA_M_APPROCCIO_2_NTC_6_4_2_1 == pytest.approx(1.0)
    assert GAMMA_R_STATICO_NTC_6_4_2_1 == pytest.approx(2.3)


def test_gamma_r_citation_is_tab_6_4_i_not_tab_6_4_ii():
    """Tab. 6.4.II NTC 2018 §6.4.3.1.1 lists resistance factors for PILE foundations; the
    gamma_R=1.0/1.8/2.3 factors for shallow-foundation bearing capacity (R1/R2/R3) are in
    Tab. 6.4.I §6.4.2.1. Citing 6.4.II here would be a wrong normative reference."""
    assert "Tab. 6.4.I" in CITAZIONE_GAMMA_R
    assert "6.4.II" not in CITAZIONE_GAMMA_R
    assert "§6.4.2.1" in CITAZIONE_GAMMA_R


def test_drained_check_passes_for_low_demand():
    esito = verifica_drenata(
        n_ed_kn=100.0, b_m=2.0, l_m=3.0, phi_k_deg=30.0, c_k_kpa=10.0, gamma_kn_m3=18.0,
        profondita_piano_posa_m=1.5)
    assert esito.passed is True
    assert esito.n_ed_kn == pytest.approx(100.0)
    r_d_atteso = esito.carico_limite.q_lim_kpa * esito.carico_limite.area_efficace.a_eff_m2 / GAMMA_R_STATICO_NTC_6_4_2_1
    assert esito.r_d_kn == pytest.approx(r_d_atteso)
    assert esito.ratio == pytest.approx(100.0 / r_d_atteso)


def test_drained_check_uses_n_ed_as_v_in_the_inclination_factors():
    """CRITICAL/HIGH finding: iq/iγ (EN 1997-1 Annex D.4) are only valid for the (H,V) pair
    actually acting; V must be N_Ed, not an independently-supplied larger value. Hand-derive:
    verifica_drenata(n_ed_kn=300, h_kn=120, ...) must match carico_limite_drenato called with
    v_kn=300 (== n_ed_kn) directly -- there is no separate v_kn to diverge from n_ed_kn."""
    atteso = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=10.0, gamma_kn_m3=18.0,
        profondita_piano_posa_m=1.5, v_kn=300.0, h_kn=120.0)
    esito = verifica_drenata(
        n_ed_kn=300.0, h_kn=120.0, b_m=2.0, l_m=3.0, phi_k_deg=30.0, c_k_kpa=10.0, gamma_kn_m3=18.0,
        profondita_piano_posa_m=1.5)
    assert esito.carico_limite.fattori_inclinazione_carico.iq == pytest.approx(
        atteso.fattori_inclinazione_carico.iq, rel=1e-9)
    assert esito.carico_limite.q_lim_kpa == pytest.approx(atteso.q_lim_kpa, rel=1e-9)


def test_verifica_drenata_has_no_separate_v_kn_parameter():
    """The old signature accepted both n_ed_kn and an independent v_kn, letting a caller inflate
    iq/iγ with a V larger than the actual demand. v_kn must no longer be an accepted keyword."""
    with pytest.raises(TypeError):
        verifica_drenata(
            n_ed_kn=100.0, v_kn=1000.0, b_m=2.0, l_m=3.0, phi_k_deg=30.0, c_k_kpa=10.0,
            gamma_kn_m3=18.0, profondita_piano_posa_m=1.5)


def test_drained_check_fails_when_demand_exceeds_capacity():
    esito = verifica_drenata(
        n_ed_kn=1.0e9, b_m=2.0, l_m=3.0, phi_k_deg=30.0, c_k_kpa=10.0, gamma_kn_m3=18.0,
        profondita_piano_posa_m=1.5)
    assert esito.passed is False
    assert esito.ratio > 1.0


def test_undrained_check_hand_verified_against_carico_limite():
    esito = verifica_non_drenata(
        n_ed_kn=200.0, b_m=2.0, l_m=3.0, cu_k_kpa=50.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5)
    assert esito.carico_limite.condizione == "non_drenata"
    assert esito.r_d_kn == pytest.approx(
        esito.carico_limite.q_lim_kpa * esito.carico_limite.area_efficace.a_eff_m2 / GAMMA_R_STATICO_NTC_6_4_2_1)


def test_seismic_option_raises_calc_error_instead_of_silently_reusing_static_formula():
    """NTC 2018 §7.11.5.3.1 requires the seismic bearing-capacity check to account for inertial
    forces in the soil below the foundation; this is not implemented (Paolucci-Pecker factors are
    'Da confermare'). sismico=True must never produce a result indistinguishable from the static
    check under a seismic label: it must raise, not silently return passed=True/False."""
    with pytest.raises(CalcError, match="[Ss]ismic"):
        verifica_drenata(
            n_ed_kn=100.0, b_m=2.0, l_m=3.0, phi_k_deg=30.0, c_k_kpa=10.0, gamma_kn_m3=18.0,
            profondita_piano_posa_m=1.5, sismico=True)


def test_seismic_option_raises_calc_error_for_undrained_too():
    with pytest.raises(CalcError):
        verifica_non_drenata(
            n_ed_kn=200.0, b_m=2.0, l_m=3.0, cu_k_kpa=50.0, gamma_kn_m3=18.0,
            profondita_piano_posa_m=1.5, sismico=True)


def test_negative_n_ed_raises_value_error():
    with pytest.raises(ValueError):
        verifica_drenata(
            n_ed_kn=-1.0, b_m=2.0, l_m=3.0, phi_k_deg=30.0, c_k_kpa=10.0, gamma_kn_m3=18.0,
            profondita_piano_posa_m=1.5)


def test_undrained_negative_n_ed_raises_value_error():
    with pytest.raises(ValueError):
        verifica_non_drenata(
            n_ed_kn=-1.0, b_m=2.0, l_m=3.0, cu_k_kpa=50.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5)
