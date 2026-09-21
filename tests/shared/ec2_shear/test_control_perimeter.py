"""§6.4.2 control perimeter, rectangular and circular columns."""
import math

import pytest

from strutture.shared.ec2_shear import control_perimeter


def test_rectangular_perimeter_at_column_face():
    result = control_perimeter("rett", 400.0, 400.0, 0.0)
    assert result.u_mm == pytest.approx(2 * (400 + 400))
    assert result.area_mm2 == pytest.approx(400 * 400)


def test_rectangular_perimeter_at_offset_matches_rounded_rectangle_formula():
    a, b, dist = 400.0, 400.0, 860.0
    result = control_perimeter("rett", a, b, dist)
    assert result.u_mm == pytest.approx(2 * (a + b) + 2 * math.pi * dist)
    assert result.area_mm2 == pytest.approx(a * b + 2 * (a + b) * dist + math.pi * dist**2)


def test_circular_perimeter():
    diameter, dist = 600.0, 300.0
    result = control_perimeter("circ", diameter, None, dist)
    assert result.u_mm == pytest.approx(math.pi * (diameter + 2 * dist))
    assert result.area_mm2 == pytest.approx(math.pi * (diameter / 2 + dist) ** 2)


def test_rectangular_requires_b():
    with pytest.raises(ValueError, match="b_mm"):
        control_perimeter("rett", 400.0, None, 100.0)


def test_unknown_shape_raises():
    with pytest.raises(ValueError, match="shape"):
        control_perimeter("triangolo", 400.0, 400.0, 100.0)  # type: ignore[arg-type]


@pytest.mark.parametrize(("a_mm", "dist_mm"), [(0.0, 100.0), (-10.0, 100.0), (400.0, -1.0)])
def test_invalid_inputs_raise(a_mm, dist_mm):
    with pytest.raises(ValueError):
        control_perimeter("rett", a_mm, 400.0, dist_mm)
