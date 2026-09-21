"""`under_center` / `ic_center`: exact 4-quadrant decomposition and physical sanity limits."""
from itertools import pairwise

import pytest

from strutture.shared.soil_stress import ic_center, newmark_corner, under_center


@pytest.mark.unit
def test_under_center_is_four_equal_quadrants() -> None:
    q, b, l, z = 78.45, 3.5, 5.0, 1.0
    expected = 4 * newmark_corner(q, b / 2, l / 2, z)
    assert under_center(q, b, l, z) == pytest.approx(expected, rel=1e-12)


@pytest.mark.unit
def test_ic_center_is_the_pure_influence_factor() -> None:
    b, l, z = 3.5, 5.0, 1.0
    q = 78.45
    assert under_center(q, b, l, z) == pytest.approx(q * ic_center(b, l, z), rel=1e-12)


@pytest.mark.unit
def test_approaches_full_pressure_at_shallow_depth() -> None:
    """As z -> 0 relative to B, L, the whole load acts directly under the centre: Δσ -> q."""
    assert under_center(100.0, 10.0, 10.0, 0.001) == pytest.approx(100.0, rel=1e-3)


@pytest.mark.unit
def test_decreases_monotonically_with_depth() -> None:
    depths = (0.5, 1.0, 2.0, 5.0, 10.0)
    values = [under_center(100.0, 4.0, 4.0, z) for z in depths]
    assert all(earlier > later for earlier, later in pairwise(values))


@pytest.mark.unit
def test_square_footing_ic_matches_brute_force_double_integral() -> None:
    """Cross-check against a direct numerical integration of the Boussinesq point-load kernel over
    the loaded unit square (independent of the closed-form corner-superposition derivation)."""
    assert ic_center(1.0, 1.0, 1.0) == pytest.approx(0.336108, rel=1e-4)
