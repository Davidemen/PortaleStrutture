"""Polygon geometry primitives (clipping, moments): pure-geometry checks independent of the
footing-pressure physics that consumes them (no_tension.py).
"""
import math

import pytest

from strutture.shared.footing_pressure.polygon import (
    area,
    clip_half_plane,
    first_moments,
    rectangle,
    second_moments,
    support,
)

pytestmark = pytest.mark.unit


def test_rectangle_area_and_moments_match_analytic_formulas():
    bx, by = 6.0, 4.0
    rect = rectangle(bx, by)
    assert area(rect) == pytest.approx(bx * by)
    assert first_moments(rect) == pytest.approx((0.0, 0.0), abs=1e-12)  # centred on the origin
    sxx, syy, sxy = second_moments(rect)
    assert sxx == pytest.approx(by * bx**3 / 12.0)  # integral of x^2 dA about the origin
    assert syy == pytest.approx(bx * by**3 / 12.0)  # integral of y^2 dA about the origin
    assert sxy == pytest.approx(0.0, abs=1e-12)  # symmetric about both axes


def test_support_function_matches_box_extremes():
    bx, by = 6.0, 4.0
    assert support(1.0, 0.0, bx, by) == pytest.approx(bx / 2.0)
    assert support(0.0, 1.0, bx, by) == pytest.approx(by / 2.0)
    assert support(math.cos(0.3), math.sin(0.3), bx, by) == pytest.approx(
        bx / 2.0 * abs(math.cos(0.3)) + by / 2.0 * abs(math.sin(0.3)))


def test_clip_half_plane_through_centre_halves_a_square():
    rect = rectangle(4.0, 4.0)
    right_half = clip_half_plane(rect, 1.0, 0.0, 0.0)  # keep x >= 0
    assert area(right_half) == pytest.approx(8.0)
    cx, cy = first_moments(right_half)
    assert cx / area(right_half) == pytest.approx(1.0)  # centroid of [0,2]x[-2,2] is at x=1
    assert cy == pytest.approx(0.0, abs=1e-12)


def test_clip_half_plane_empty_when_line_misses_the_polygon():
    rect = rectangle(2.0, 2.0)
    assert clip_half_plane(rect, 1.0, 0.0, 10.0) == ()


def test_clip_half_plane_full_when_line_is_outside_the_other_way():
    rect = rectangle(2.0, 2.0)
    kept = clip_half_plane(rect, 1.0, 0.0, -10.0)
    assert area(kept) == pytest.approx(area(rect))


def test_clipped_triangle_moments_match_hand_computation():
    # Clip the unit square [0,1]x[0,1] by x+y>=1: the triangle (1,0)-(1,1)-(0,1).
    square = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    triangle = clip_half_plane(square, 1.0, 1.0, 1.0)
    assert area(triangle) == pytest.approx(0.5)
    mx, my = first_moments(triangle)
    # Centroid of that right triangle is (2/3, 2/3) -> first moments = area * centroid.
    assert (mx / 0.5, my / 0.5) == pytest.approx((2.0 / 3.0, 2.0 / 3.0))
