"""Stirrup area-per-metre unit tests."""
import math

import pytest

from strutture.shared.rebar_catalog import asw_per_m

pytestmark = pytest.mark.unit


def test_asw_per_m_two_legs_phi8_at_200mm():
    # Asw = 2 legs * area(Ø8) = 2*50.265 = 100.53 mm^2; per metre at 200mm spacing: *5 = 502.65
    expected = 2 * (math.pi / 4 * 8.0**2) * 1000.0 / 200.0
    assert asw_per_m(8.0, 2, 200.0) == pytest.approx(expected, rel=1e-9)
    assert asw_per_m(8.0, 2, 200.0) == pytest.approx(502.65, rel=1e-3)


def test_asw_per_m_rejects_non_positive_legs():
    with pytest.raises(ValueError):
        asw_per_m(8.0, 0, 200.0)


def test_asw_per_m_rejects_non_positive_spacing():
    with pytest.raises(ValueError):
        asw_per_m(8.0, 2, 0.0)
