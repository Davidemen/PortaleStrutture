"""Meyerhof effective area B' = B - 2eB, L' = L - 2eL, swapped so B' <= L'."""
import math

import pytest

from strutture.shared.capacita_portante.area_efficace import area_efficace, area_efficace_nastriforme
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit


def test_centred_load_keeps_full_area():
    area = area_efficace(2.0, 3.0)
    assert area.b_eff_m == pytest.approx(2.0)
    assert area.l_eff_m == pytest.approx(3.0)
    assert area.a_eff_m2 == pytest.approx(6.0)
    assert area.nastriforme is False


def test_eccentric_load_reduces_dimensions_by_twice_the_eccentricity():
    area = area_efficace(2.0, 3.0, eb_m=0.2, el_m=0.3)
    assert area.b_eff_m == pytest.approx(2.0 - 0.4)
    assert area.l_eff_m == pytest.approx(3.0 - 0.6)
    assert area.a_eff_m2 == pytest.approx((2.0 - 0.4) * (3.0 - 0.6))


def test_swaps_so_b_prime_is_never_greater_than_l_prime():
    area = area_efficace(4.0, 2.0)  # B > L before the swap
    assert area.b_eff_m <= area.l_eff_m
    assert area.b_eff_m == pytest.approx(2.0)
    assert area.l_eff_m == pytest.approx(4.0)


def test_negative_dimensions_raise_calc_error_in_italian():
    with pytest.raises(CalcError, match="positive"):
        area_efficace(-1.0, 3.0)


def test_eccentricity_ge_half_width_raises_calc_error():
    with pytest.raises(CalcError, match="eccentricit"):
        area_efficace(2.0, 3.0, eb_m=1.0)


def test_eccentricity_ge_half_length_raises_calc_error():
    with pytest.raises(CalcError, match="eccentricit"):
        area_efficace(2.0, 3.0, el_m=1.5)


def test_strip_footing_area_is_per_metre_of_run():
    area = area_efficace_nastriforme(2.0, eb_m=0.2)
    assert area.nastriforme is True
    assert area.b_eff_m == pytest.approx(1.6)
    assert area.l_eff_m == math.inf
    assert area.a_eff_m2 == pytest.approx(1.6)


def test_strip_footing_eccentricity_ge_half_width_raises_calc_error():
    with pytest.raises(CalcError):
        area_efficace_nastriforme(2.0, eb_m=1.5)


def test_strip_footing_negative_width_raises_calc_error():
    with pytest.raises(CalcError, match="positiva"):
        area_efficace_nastriforme(-2.0)


def test_swap_sets_scambiato_flag_true_when_physical_b_eff_exceeds_l_eff():
    """B=4, L=2 (no eccentricity): physical b_eff=4 > physical l_eff=2, so area_efficace swaps
    them to keep b_eff_m<=l_eff_m. `scambiato` must flag that the swap happened, so callers that
    need to know which physical axis (B or L) now sits in b_eff_m/l_eff_m can compensate."""
    area = area_efficace(4.0, 2.0)
    assert area.scambiato is True


def test_no_swap_when_physical_b_eff_already_le_l_eff():
    area = area_efficace(2.0, 3.0)
    assert area.scambiato is False


def test_eccentricity_alone_can_flip_scambiato():
    """B=2, L=3, eL=1.2: physical b_eff=2.0, physical l_eff=3-2*1.2=0.6 -> b_eff > l_eff -> swap."""
    area = area_efficace(2.0, 3.0, el_m=1.2)
    assert area.scambiato is True
    assert area.b_eff_m == pytest.approx(0.6)
    assert area.l_eff_m == pytest.approx(2.0)


def test_strip_footing_never_swaps():
    area = area_efficace_nastriforme(2.0, eb_m=0.2)
    assert area.scambiato is False
