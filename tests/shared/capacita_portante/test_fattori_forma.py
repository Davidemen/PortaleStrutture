"""sq, sγ, sc shape factors (EN 1997-1 Annex D.2/D.3)."""
import math

import pytest

from strutture.shared.capacita_portante.fattori_forma import (
    STRIP_FOOTING_SHAPE_FACTORS,
    fattori_forma,
    fattori_forma_non_drenata,
)
from strutture.shared.capacita_portante.fattori_portanza import fattori_portanza

pytestmark = pytest.mark.unit


def test_shape_factors_hand_computed_b_2_l_4_phi_30():
    # B'=2, L'=4 -> B'/L'=0.5; phi'=30 -> sin(30)=0.5, Nq=18.401122.
    nq = fattori_portanza(30.0).nq
    fattori = fattori_forma(2.0, 4.0, 30.0, nq)
    assert fattori.sq == pytest.approx(1.0 + 0.5 * 0.5)
    assert fattori.sgamma == pytest.approx(1.0 - 0.3 * 0.5)
    assert fattori.sc == pytest.approx((fattori.sq * nq - 1.0) / (nq - 1.0))


def test_strip_footing_shape_factors_are_all_one():
    fattori = fattori_forma(2.0, math.inf, 30.0, 18.4, nastriforme=True)
    assert fattori == STRIP_FOOTING_SHAPE_FACTORS


def test_phi_zero_limit_sc_matches_undrained_form():
    fattori = fattori_forma(2.0, 4.0, 0.0, 1.0)
    assert fattori.sc == pytest.approx(1.0 + 0.2 * 0.5)
    assert fattori.sc == pytest.approx(fattori_forma_non_drenata(2.0, 4.0))


def test_undrained_sc_strip_footing_is_one():
    assert fattori_forma_non_drenata(2.0, 4.0, nastriforme=True) == pytest.approx(1.0)


def test_square_footing_ratio_one():
    nq = fattori_portanza(25.0).nq
    fattori = fattori_forma(3.0, 3.0, 25.0, nq)
    assert fattori.sgamma == pytest.approx(0.7)


def test_invalid_dimensions_raise_value_error():
    with pytest.raises(ValueError):
        fattori_forma(0.0, 3.0, 30.0, 10.0)


def test_non_drenata_invalid_dimensions_raise_value_error():
    with pytest.raises(ValueError):
        fattori_forma_non_drenata(0.0, 3.0)
