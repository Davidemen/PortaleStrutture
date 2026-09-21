"""Unit tests for Ss/Cc (NTC 2018 Tab. 3.2.IV) — including the categoria-B lower-clip divergence."""
import pytest

from strutture.shared.ntc_site_seismic.stratigrafia import (
    coefficiente_correzione_cc,
    fattore_amplificazione_ss,
)

pytestmark = pytest.mark.unit


def test_ss_categoria_a_is_constant():
    assert fattore_amplificazione_ss("A", f0=2.5, ag_g=1.0) == pytest.approx(1.0)


def test_cc_categoria_a_is_constant():
    assert coefficiente_correzione_cc("A", tc_star_s=0.3) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("categoria", "tc_star", "cc"),
    [
        ("B", 0.272, 1.42718050386463),
        ("C", 0.35, 1.48472781405157),
        ("D", 0.4, 1.97642353760524),
        ("E", 0.3, 1.86144127018245),
    ],
)
def test_cc_per_categoria(categoria, tc_star, cc):
    assert coefficiente_correzione_cc(categoria, tc_star) == pytest.approx(cc, rel=1e-9)


def test_ss_categoria_b_upper_clip():
    # F0*ag ~ 0 -> raw value above the 1.20 upper bound.
    assert fattore_amplificazione_ss("B", f0=1.0, ag_g=0.0) == pytest.approx(1.2)


def test_ss_categoria_b_high_fa_fixed_behaviour_uses_ntc_floor_1_00():
    # 1.40 - 0.40*2.5*1.1 = 0.30 -> below both clips; fixed behaviour floors at 1.00 (Tab. 3.2.IV).
    assert fattore_amplificazione_ss("B", f0=2.5, ag_g=1.1, legacy_compat=False) == pytest.approx(1.00)


def test_ss_categoria_b_high_fa_legacy_compat_reproduces_sheet_bug():
    # legacy_compat=True reproduces the sheet's wrong 0.40 lower clip (Tabelle!E8 bug).
    assert fattore_amplificazione_ss("B", f0=2.5, ag_g=1.1, legacy_compat=True) == pytest.approx(0.40)


def test_ss_categoria_c_bounds():
    assert fattore_amplificazione_ss("C", f0=1.0, ag_g=0.0) == pytest.approx(1.5)
    assert fattore_amplificazione_ss("C", f0=3.0, ag_g=1.0) == pytest.approx(1.0)


def test_ss_categoria_d_bounds():
    assert fattore_amplificazione_ss("D", f0=1.0, ag_g=0.0) == pytest.approx(1.8)
    assert fattore_amplificazione_ss("D", f0=3.0, ag_g=1.0) == pytest.approx(0.9)


def test_ss_categoria_e_bounds():
    assert fattore_amplificazione_ss("E", f0=1.0, ag_g=0.0) == pytest.approx(1.6)
    assert fattore_amplificazione_ss("E", f0=3.0, ag_g=1.0) == pytest.approx(1.0)


def test_ss_unknown_categoria_raises():
    with pytest.raises(ValueError):
        fattore_amplificazione_ss("Z", f0=1.0, ag_g=0.1)


def test_cc_unknown_categoria_raises():
    with pytest.raises(ValueError):
        coefficiente_correzione_cc("Z", tc_star_s=0.3)
