"""Unit tests for design friction angles φd, δd (rows 45-50/80-81, cols K/M).

NTC2018 Tab. 6.2.II defines γφ' as a factor on tan(φ'), not on the angle itself: φ'd =
atan(tan(φ'k)/γφ'). The sheet (`legacy_compat=True`) instead divides the angle directly. The two
only coincide for γφ,terr = 1 (M1 rows)."""
import math

import pytest

from strutture.members.muro.angoli_progetto import delta_d_rad, phi_d_rad

pytestmark = pytest.mark.unit


def test_phi_d_rad_fixed_behaviour_divides_tan_by_gamma_phi_terr():
    """legacy_compat=False (default): φ'd = atan(tan(φ'k)/γφ'), NTC2018 Tab. 6.2.II."""
    assert phi_d_rad(30.0, 1.25) == pytest.approx(math.atan(math.tan(math.radians(30.0)) / 1.25))
    assert phi_d_rad(30.0, 1.25) == pytest.approx(math.radians(24.79), abs=1e-3)


def test_phi_d_rad_legacy_compat_divides_the_angle_itself():
    """legacy_compat=True reproduces the sheet's (non-normative) angle division."""
    assert phi_d_rad(30.69, 1.25, legacy_compat=True) == pytest.approx(math.radians(30.69) / 1.25)


def test_phi_d_rad_gamma_one_is_identical_in_both_modes():
    """γφ,terr=1 (M1 rows): atan(tan(x)/1) == x, so both modes coincide."""
    assert phi_d_rad(30.69, 1.0, legacy_compat=False) == pytest.approx(phi_d_rad(30.69, 1.0, legacy_compat=True))


def test_delta_d_rad_zero_delta_is_zero():
    assert delta_d_rad(0.0, 1.25) == pytest.approx(0.0)
    assert delta_d_rad(0.0, 1.25, legacy_compat=True) == pytest.approx(0.0)


def test_delta_d_rad_nonzero_fixed_behaviour():
    assert delta_d_rad(15.0, 1.0) == pytest.approx(math.radians(15.0))


def test_delta_d_rad_nonzero_legacy_vs_fixed_diverge_when_gamma_not_one():
    legacy = delta_d_rad(15.0, 1.25, legacy_compat=True)
    fixed = delta_d_rad(15.0, 1.25, legacy_compat=False)
    assert legacy == pytest.approx(math.radians(15.0) / 1.25)
    assert fixed == pytest.approx(math.atan(math.tan(math.radians(15.0)) / 1.25))
    assert legacy != pytest.approx(fixed)
