"""Unit tests for `ka_coulomb` (NTC2018 §6.5.3.1.1, muro-sostegno row 56)."""
import math

import pytest

from strutture.members.muro.coulomb import ka_coulomb

pytestmark = pytest.mark.unit


def test_ka_coulomb_tratto_a_str1():
    phi_d = math.radians(30.69) / 1.0
    delta_d = math.atan(math.tan(math.radians(0.0))) / 1.0
    ka = ka_coulomb(phi_d_rad=phi_d, delta_d_rad=delta_d, beta_rad=0.0, psi_rad=math.radians(90))
    assert ka == pytest.approx(0.324159, rel=1e-5)


def test_ka_coulomb_vertical_wall_no_friction_matches_rankine():
    """δ=β=0, ψ=90° (vertical, frictionless) -> Coulomb reduces to Rankine Ka = tan²(45° - φ/2)."""
    phi_deg = 28.0
    phi_d = math.radians(phi_deg)
    ka = ka_coulomb(phi_d_rad=phi_d, delta_d_rad=0.0, beta_rad=0.0, psi_rad=math.radians(90))
    atteso = math.tan(math.radians(45 - phi_deg / 2)) ** 2
    assert ka == pytest.approx(atteso, rel=1e-9)


def test_ka_coulomb_slope_steeper_than_friction_angle_uses_else_branch():
    """β > φd: the sheet's `IF(β<=φd, ..., U/V)` falls to the simpler U/V branch."""
    phi_d = math.radians(20.0)
    beta = math.radians(25.0)
    ka = ka_coulomb(phi_d_rad=phi_d, delta_d_rad=0.0, beta_rad=beta, psi_rad=math.radians(90))
    u = math.sin(math.radians(90) + phi_d) ** 2
    v = math.sin(math.radians(90)) ** 2 * math.sin(math.radians(90) - 0.0)
    assert ka == pytest.approx(u / v)
