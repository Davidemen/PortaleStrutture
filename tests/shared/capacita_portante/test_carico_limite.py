"""q_lim (EN 1997-1 Annex D): drained/undrained, water table, strip-footing limit, monotonicity,
phi'->0 limit, invalid inputs. Derivations are hand-computed in each test's docstring/body from
the closed forms, independently of the module under test (`fattori_*` closed forms recomputed
inline rather than re-using the module's own helpers, to avoid a circular check).
"""
import math

import pytest

from strutture.shared.capacita_portante.carico_limite import carico_limite_drenato, carico_limite_non_drenato
from strutture.shared.capacita_portante.fattori_inclinazione import esponente_m
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit

_GAMMA_W = 9.80665


def _nq_nc_ngamma(phi_deg: float) -> tuple[float, float, float]:
    phi_rad = math.radians(phi_deg)
    nq = math.exp(math.pi * math.tan(phi_rad)) * math.tan(math.radians(45.0) + phi_rad / 2.0) ** 2
    return nq, (nq - 1.0) / math.tan(phi_rad), 2.0 * (nq - 1.0) * math.tan(phi_rad)


def test_centred_case_hand_computed():
    """B=L'=2x3 m (centred, B'=B=2, L'=L=3), phi'=30 deg, c'=0, gamma=18 kN/m3, D=1.5 m, V=1000 kN, H=0.
    q' = gamma*D = 27 kPa. B'/L' = 2/3. sq = 1 + (2/3)*sin(30) = 1.33333. sgamma = 1 - 0.3*(2/3) = 0.8.
    iq = igamma = bq = bgamma = 1 (H=0, alpha=0). q_lim = q'*Nq*sq + 0.5*gamma*B'*Ngamma*sgamma (c'=0 kills the c term).
    """
    nq, _, ngamma = _nq_nc_ngamma(30.0)
    ratio = 2.0 / 3.0
    sq = 1.0 + ratio * math.sin(math.radians(30.0))
    sgamma = 1.0 - 0.3 * ratio
    q_eff = 18.0 * 1.5
    atteso = q_eff * nq * sq + 0.5 * 18.0 * 2.0 * ngamma * sgamma
    risultato = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)
    assert risultato.q_lim_kpa == pytest.approx(atteso, rel=1e-9)
    assert risultato.q_eff_kpa == pytest.approx(27.0)
    assert risultato.gamma_eff_kn_m3 == pytest.approx(18.0)


def test_eccentric_case_reduces_area_and_bearing_pressure():
    centrato = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=10.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)
    eccentrico = carico_limite_drenato(
        b_m=2.0, l_m=3.0, eb_m=0.3, phi_deg=30.0, c_kpa=10.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)
    assert eccentrico.area_efficace.b_eff_m == pytest.approx(2.0 - 0.6)
    assert eccentrico.area_efficace.a_eff_m2 < centrato.area_efficace.a_eff_m2


def test_inclined_case_hand_computed_against_zero_h_case():
    senza_h = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)
    con_h = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0, h_kn=200.0)
    assert con_h.fattori_inclinazione_carico.iq == pytest.approx(0.8 ** con_h.fattori_inclinazione_carico.m)
    assert con_h.q_lim_kpa < senza_h.q_lim_kpa


def test_more_eccentricity_never_increases_q_lim_times_area():
    resistenze = []
    for eb in (0.0, 0.1, 0.2, 0.3):
        r = carico_limite_drenato(
            b_m=2.0, l_m=3.0, eb_m=eb, phi_deg=30.0, c_kpa=10.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)
        resistenze.append(r.q_lim_kpa * r.area_efficace.a_eff_m2)
    assert resistenze == sorted(resistenze, reverse=True)


def test_more_inclination_never_increases_q_lim():
    valori = [
        carico_limite_drenato(
            b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0, h_kn=h).q_lim_kpa
        for h in (0.0, 100.0, 200.0, 300.0)
    ]
    assert valori == sorted(valori, reverse=True)


def test_water_table_below_base_has_no_effect():
    senza_falda = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)
    falda_profonda = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0,
        profondita_falda_m=50.0)
    assert falda_profonda.q_lim_kpa == pytest.approx(senza_falda.q_lim_kpa)
    assert falda_profonda.gamma_eff_kn_m3 == pytest.approx(18.0)


def test_water_table_at_base_uses_buoyant_gamma_but_not_q_eff():
    risultato = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0,
        profondita_falda_m=1.5)
    assert risultato.gamma_eff_kn_m3 == pytest.approx(18.0 - _GAMMA_W)
    assert risultato.q_eff_kpa == pytest.approx(18.0 * 1.5)  # q' still above the water table


def test_water_table_above_base_reduces_both_q_eff_and_gamma_eff():
    risultato = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0,
        profondita_falda_m=0.5)
    atteso_q_eff = 18.0 * 0.5 + (18.0 - _GAMMA_W) * (1.5 - 0.5)
    assert risultato.q_eff_kpa == pytest.approx(atteso_q_eff)
    assert risultato.gamma_eff_kn_m3 == pytest.approx(18.0 - _GAMMA_W)


def test_water_table_lowers_q_lim_versus_no_water_table():
    senza_falda = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)
    con_falda = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0,
        profondita_falda_m=0.0)
    assert con_falda.q_lim_kpa < senza_falda.q_lim_kpa


def test_strip_footing_matches_the_limit_of_a_very_long_rectangle():
    strip = carico_limite_drenato(
        b_m=2.0, l_m=2.0, nastriforme=True, phi_deg=30.0, c_kpa=5.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5,
        v_kn=1000.0)
    lungo = carico_limite_drenato(
        b_m=2.0, l_m=2000.0, phi_deg=30.0, c_kpa=5.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)
    assert strip.q_lim_kpa == pytest.approx(lungo.q_lim_kpa, rel=1e-3)


def test_drained_phi_near_zero_matches_undrained_with_cu_equal_c():
    quasi_zero = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=1e-3, c_kpa=50.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)
    non_drenato = carico_limite_non_drenato(
        b_m=2.0, l_m=3.0, cu_kpa=50.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5)
    assert quasi_zero.q_lim_kpa == pytest.approx(non_drenato.q_lim_kpa, rel=1e-2)


def test_undrained_hand_computed():
    # (pi+2)*cu*bc*sc*ic + q; H=0,alpha=0 -> bc=ic=1; B'=2,L'=3 -> sc=1+0.2*(2/3).
    risultato = carico_limite_non_drenato(
        b_m=2.0, l_m=3.0, cu_kpa=50.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5)
    sc = 1.0 + 0.2 * (2.0 / 3.0)
    atteso = (math.pi + 2.0) * 50.0 * 1.0 * sc * 1.0 + 18.0 * 1.5
    assert risultato.q_lim_kpa == pytest.approx(atteso)


def test_undrained_h_exceeding_a_eff_cu_raises_calc_error_in_italian():
    with pytest.raises(CalcError, match="non drenata"):
        carico_limite_non_drenato(
            b_m=2.0, l_m=3.0, cu_kpa=10.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, h_kn=1000.0)


def test_drained_h_exceeding_available_resistance_raises_calc_error():
    with pytest.raises(CalcError):
        carico_limite_drenato(
            b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=100.0,
            h_kn=200.0)


def test_negative_dimensions_raise_calc_error():
    with pytest.raises(CalcError):
        carico_limite_drenato(
            b_m=-2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)


def test_eccentricity_ge_half_width_raises_calc_error():
    with pytest.raises(CalcError):
        carico_limite_drenato(
            b_m=2.0, l_m=3.0, eb_m=1.5, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)


def test_phi_zero_drained_call_raises_calc_error():
    with pytest.raises(CalcError):
        carico_limite_drenato(
            b_m=2.0, l_m=3.0, phi_deg=0.0, c_kpa=50.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)


def test_water_table_partly_within_the_b_prime_band_interpolates_gamma_eff():
    # D=1.5, B'=2 -> band [1.5, 3.5]; falda at 2.5 -> halfway (frazione=0.5).
    risultato = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0,
        profondita_falda_m=2.5)
    gamma_sub = 18.0 - _GAMMA_W
    atteso = gamma_sub + 0.5 * (18.0 - gamma_sub)
    assert risultato.gamma_eff_kn_m3 == pytest.approx(atteso)


def test_direzione_h_l_is_mapped_correctly_when_eccentric_swap_flips_axes():
    """EN 1997-1 Annex D.4: B=2 m, L=3 m, eB=0, eL=1.2 m. Physical b_eff (B direction) = 2.0,
    physical l_eff (L direction) = 3 - 2*1.2 = 0.6. `area_efficace` swaps them to keep
    b_eff_m<=l_eff_m: b_eff_m=0.6 (holds the physical L quantity), l_eff_m=2.0 (holds the
    physical B quantity), scambiato=True. `direzione_h='L'` means H acts along the PHYSICAL L
    axis, whose effective length (0.6) is now stored in area.b_eff_m, i.e. the "B'" slot of the
    m formula: m = (2 + 0.6/2.0) / (1 + 0.6/2.0) = 2.3/1.3 = 1.7692307...
    With c'=0 (A'c'cotphi' term vanishes), V=500 kN, H=100 kN: iq = (1 - 100/500)^m = 0.8^m.
    """
    m_atteso = (2.0 + 0.6 / 2.0) / (1.0 + 0.6 / 2.0)
    iq_atteso = 0.8**m_atteso
    risultato = carico_limite_drenato(
        b_m=2.0, l_m=3.0, el_m=1.2, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0,
        profondita_piano_posa_m=1.5, v_kn=500.0, h_kn=100.0, direzione_h="L")
    assert risultato.area_efficace.scambiato is True
    assert risultato.fattori_inclinazione_carico.m == pytest.approx(m_atteso, rel=1e-9)
    assert risultato.fattori_inclinazione_carico.iq == pytest.approx(iq_atteso, rel=1e-9)


def test_direzione_h_b_is_mapped_correctly_when_eccentric_swap_flips_axes():
    """Same footing as above, H now along the PHYSICAL B axis (direzione_h='B'): its effective
    length (2.0) is stored in area.l_eff_m after the swap, i.e. the "L'" slot of the m formula:
    m = (2 + 2.0/0.6) / (1 + 2.0/0.6) = 1.230769... (this is the value the CRITICAL finding
    reports the unfixed code wrongly returns for direzione_h='L').
    """
    m_atteso = (2.0 + 2.0 / 0.6) / (1.0 + 2.0 / 0.6)
    risultato = carico_limite_drenato(
        b_m=2.0, l_m=3.0, el_m=1.2, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0,
        profondita_piano_posa_m=1.5, v_kn=500.0, h_kn=100.0, direzione_h="B")
    assert risultato.fattori_inclinazione_carico.m == pytest.approx(m_atteso, rel=1e-9)


def test_direzione_h_theta_is_complemented_when_eccentric_swap_flips_axes():
    """theta_deg is measured from the physical L axis. After the swap (b_eff_m=0.6 holds
    physical L, l_eff_m=2.0 holds physical B), a physical theta must become 90-theta so that
    esponente_m's own theta (measured from whatever now sits in l_eff_m) points at the same
    physical direction. theta_deg=30 (physical) -> effective theta=60."""
    m_atteso = esponente_m(0.6, 2.0, direzione="theta", theta_deg=60.0)
    risultato = carico_limite_drenato(
        b_m=2.0, l_m=3.0, el_m=1.2, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=18.0,
        profondita_piano_posa_m=1.5, v_kn=500.0, h_kn=100.0, direzione_h="theta", theta_deg=30.0)
    assert risultato.fattori_inclinazione_carico.m == pytest.approx(m_atteso, rel=1e-9)


def test_non_positive_gamma_raises_value_error():
    with pytest.raises(ValueError):
        carico_limite_drenato(
            b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=0.0, gamma_kn_m3=0.0, profondita_piano_posa_m=1.5, v_kn=1000.0)


def test_undrained_non_positive_cu_raises_calc_error():
    with pytest.raises(CalcError):
        carico_limite_non_drenato(b_m=2.0, l_m=3.0, cu_kpa=0.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5)


def test_undrained_non_positive_gamma_raises_value_error():
    with pytest.raises(ValueError):
        carico_limite_non_drenato(b_m=2.0, l_m=3.0, cu_kpa=50.0, gamma_kn_m3=-1.0, profondita_piano_posa_m=1.5)


def test_hansen_depth_factors_phi_zero_branch():
    from strutture.shared.capacita_portante._fattori_profondita_hansen import (
        fattore_profondita_dc,
        fattore_profondita_dq,
    )

    assert fattore_profondita_dq(0.0, 1.5, 2.0) == pytest.approx(1.0)
    dc = fattore_profondita_dc(0.0, 1.5, 2.0, dq=1.0, nc=5.14)
    assert dc == pytest.approx(1.0 + 0.4 * min(1.5 / 2.0, 1.0))


def test_hansen_depth_factors_are_off_by_default_and_flagged_when_enabled():
    senza = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=10.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0)
    con = carico_limite_drenato(
        b_m=2.0, l_m=3.0, phi_deg=30.0, c_kpa=10.0, gamma_kn_m3=18.0, profondita_piano_posa_m=1.5, v_kn=1000.0,
        fattori_profondita=True)
    assert senza.avviso_fattori_profondita is None
    assert con.avviso_fattori_profondita is not None
    assert con.q_lim_kpa > senza.q_lim_kpa
