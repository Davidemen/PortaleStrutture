"""Hand-computed closed-form checks for rect/circle/equivalent_square."""
import math

import pytest

from strutture.shared.section_geometry import circle, equivalent_square, rect

pytestmark = pytest.mark.unit


def test_rect_300x500():
    result = rect(300.0, 500.0)
    assert result.area_mm2 == pytest.approx(150_000.0)
    assert result.inertia_mm4 == pytest.approx(300.0 * 500.0**3 / 12.0)
    assert result.inertia_mm4 == pytest.approx(3_125_000_000.0)
    assert result.radius_of_gyration_mm == pytest.approx(500.0 / math.sqrt(12.0), rel=1e-9)
    assert result.section_modulus_mm3 == pytest.approx(3_125_000_000.0 / 250.0)


@pytest.mark.parametrize(("b", "h"), [(0.0, 500.0), (300.0, 0.0), (-1.0, 500.0)])
def test_rect_rejects_non_positive_dimensions(b, h):
    with pytest.raises(ValueError):
        rect(b, h)


def test_circle_diameter_200():
    result = circle(200.0)
    expected_area = math.pi / 4 * 200.0**2
    expected_inertia = math.pi / 64 * 200.0**4
    assert result.area_mm2 == pytest.approx(expected_area)
    assert result.inertia_mm4 == pytest.approx(expected_inertia)
    assert result.radius_of_gyration_mm == pytest.approx(200.0 / 4.0, rel=1e-9)  # i = D/4 for a circle
    assert result.section_modulus_mm3 == pytest.approx(expected_inertia / 100.0)


def test_circle_rejects_non_positive_diameter():
    with pytest.raises(ValueError):
        circle(0.0)


def test_equivalent_square_of_10000_is_100():
    assert equivalent_square(10_000.0) == pytest.approx(100.0)


def test_equivalent_square_rejects_non_positive_area():
    with pytest.raises(ValueError):
        equivalent_square(0.0)
