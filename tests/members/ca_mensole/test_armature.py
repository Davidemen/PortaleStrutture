"""Unit tests for `strutture.members.ca_mensole.armature` (H20, H21, H23)."""
import math

import pytest

from strutture.members.ca_mensole.armature import armature


@pytest.mark.unit
def test_armature_short_span_branch() -> None:
    """a < 0.5h -> As,lnk = 0.25*As,hor."""
    result = armature(n_hor=8, phi_hor_mm=12, n_incl=0, phi_incl_mm=0, a_mm=177, h_mm=450, ped_kN=136, fyd_MPa=391.304347826087)
    assert result.as_hor_mm2 == pytest.approx(8 * math.pi / 4 * 12**2)
    assert result.as_incl_mm2 == pytest.approx(0)
    assert result.as_lnk_min_mm2 == pytest.approx(0.25 * result.as_hor_mm2)


@pytest.mark.unit
def test_armature_long_span_branch() -> None:
    """a >= 0.5h -> As,lnk = 0.5*PEd*1000/fyd (boundary a == 0.5h included in this branch)."""
    result = armature(n_hor=6, phi_hor_mm=14, n_incl=0, phi_incl_mm=0, a_mm=225, h_mm=450, ped_kN=100, fyd_MPa=273.913043478261)
    assert result.as_lnk_min_mm2 == pytest.approx(0.5 * 100 * 1000 / 273.913043478261)


@pytest.mark.unit
def test_armature_inclined_bars() -> None:
    result = armature(n_hor=8, phi_hor_mm=12, n_incl=4, phi_incl_mm=10, a_mm=177, h_mm=450, ped_kN=136, fyd_MPa=391.304347826087)
    assert result.as_incl_mm2 == pytest.approx(4 * math.pi / 4 * 10**2)


@pytest.mark.unit
def test_armature_zero_incl_bars_no_diameter_error() -> None:
    """n_incl=0 with phi_incl_mm=0 (sheet default) must not raise (bars_area rejects diameter<=0)."""
    result = armature(n_hor=8, phi_hor_mm=12, n_incl=0, phi_incl_mm=0, a_mm=177, h_mm=450, ped_kN=136, fyd_MPa=391.304347826087)
    assert result.as_incl_mm2 == 0.0
