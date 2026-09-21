"""No-tension biaxial solver: equilibrium, closed-form agreement, symmetry, convergence."""
import itertools
import math

import pytest

from strutture.shared.footing_pressure.no_tension import biaxial_no_tension
from strutture.shared.footing_pressure.polygon import area as polygon_area
from strutture.shared.footing_pressure.polygon import clip_half_plane, first_moments, rectangle, second_moments
from strutture.shared.footing_pressure.uniaxial import uniaxial

pytestmark = pytest.mark.unit


def _integrate_pressure(solution, ex_m, ey_m, bx_m, by_m, n_kn):
    """Re-integrate the returned plane over its own compressed polygon: independent re-derivation
    of (N, N*ex, N*ey) from (theta, offset, k), not just trusting the solver's own bookkeeping.
    """
    na = solution.neutral_axis
    nx, ny = math.cos(na.theta_rad), math.sin(na.theta_rad)
    polygon = clip_half_plane(rectangle(bx_m, by_m), nx, ny, na.offset_m)
    area_m2 = polygon_area(polygon)
    mx1, my1 = first_moments(polygon)
    sxx, syy, sxy = second_moments(polygon)
    force = na.k_kpa_m * ((nx * mx1 + ny * my1) - na.offset_m * area_m2)
    mx_first = na.k_kpa_m * ((nx * sxx + ny * sxy) - na.offset_m * mx1)
    my_first = na.k_kpa_m * ((nx * sxy + ny * syy) - na.offset_m * my1)
    return force, mx_first, my_first


@pytest.mark.parametrize(("ex_m", "ey_m"), [(1.3, 0.9), (-0.9, 0.7), (0.3, 1.9), (-1.4, -1.1), (1.9, 0.05)])
def test_equilibrium_force_and_moments_match_target(ex_m, ey_m):
    n_kn, bx_m, by_m = 1500.0, 4.0, 5.0
    solution = biaxial_no_tension(n_kn, ex_m, ey_m, bx_m, by_m)
    force, mx_first, my_first = _integrate_pressure(solution, ex_m, ey_m, bx_m, by_m, n_kn)
    assert force == pytest.approx(n_kn, rel=1e-6)
    assert mx_first == pytest.approx(n_kn * ex_m, rel=1e-6, abs=1e-6)
    assert my_first == pytest.approx(n_kn * ey_m, rel=1e-6, abs=1e-6)


def test_zero_at_kern_boundary_reproduces_uniaxial_closed_form_along_x():
    n_kn, bx_m, by_m, ex_m = 1000.0, 4.0, 5.0, 1.2  # outside bx/6=0.667, ey=0
    solution = biaxial_no_tension(n_kn, ex_m, 0.0, bx_m, by_m)
    expected = uniaxial(n_kn, n_kn * ex_m, by_m, bx_m)  # l=bx (bending direction), b=by
    assert solution.sigma_max_kpa == pytest.approx(expected.sigma_max_kpa, rel=1e-6)
    assert solution.compressed_ratio * bx_m == pytest.approx(expected.contact_len_m, rel=1e-6)


def test_zero_at_kern_boundary_reproduces_uniaxial_closed_form_along_y():
    n_kn, bx_m, by_m, ey_m = 1000.0, 4.0, 5.0, 1.8  # outside by/6=0.833, ex=0
    solution = biaxial_no_tension(n_kn, 0.0, ey_m, bx_m, by_m)
    expected = uniaxial(n_kn, n_kn * ey_m, bx_m, by_m)
    assert solution.sigma_max_kpa == pytest.approx(expected.sigma_max_kpa, rel=1e-6)
    assert solution.compressed_ratio * by_m == pytest.approx(expected.contact_len_m, rel=1e-6)


def test_symmetric_footing_swap_x_y_gives_identical_pressures():
    n_kn, side, ex_m, ey_m = 1200.0, 4.0, 1.3, 0.85
    result = biaxial_no_tension(n_kn, ex_m, ey_m, side, side)
    swapped = biaxial_no_tension(n_kn, ey_m, ex_m, side, side)
    assert swapped.sigma_max_kpa == pytest.approx(result.sigma_max_kpa, rel=1e-8)
    assert swapped.compressed_ratio == pytest.approx(result.compressed_ratio, rel=1e-8)


def test_negating_both_eccentricities_mirrors_the_solution():
    n_kn, bx_m, by_m, ex_m, ey_m = 1200.0, 4.0, 6.0, 1.1, 1.4
    result = biaxial_no_tension(n_kn, ex_m, ey_m, bx_m, by_m)
    mirrored = biaxial_no_tension(n_kn, -ex_m, -ey_m, bx_m, by_m)
    assert mirrored.sigma_max_kpa == pytest.approx(result.sigma_max_kpa, rel=1e-8)
    assert mirrored.compressed_ratio == pytest.approx(result.compressed_ratio, rel=1e-8)


def test_monotonic_sigma_max_as_eccentricity_grows_along_the_diagonal():
    n_kn, bx_m, by_m = 1000.0, 4.0, 4.0
    fractions = (0.3, 0.5, 0.7, 0.9, 0.95, 0.99)
    sigmas = []
    for f in fractions:
        ex_m = ey_m = f * (bx_m / 2.0) / math.sqrt(2.0) * 0.999  # stays inside the footing
        sigmas.append(biaxial_no_tension(n_kn, ex_m, ey_m, bx_m, by_m).sigma_max_kpa)
    assert sigmas == sorted(sigmas)
    ratios = [biaxial_no_tension(n_kn, f * (bx_m / 2.0) / math.sqrt(2.0) * 0.999,
                                  f * (bx_m / 2.0) / math.sqrt(2.0) * 0.999, bx_m, by_m).compressed_ratio
              for f in fractions]
    assert ratios == sorted(ratios, reverse=True)


@pytest.mark.parametrize(("fx", "fy", "sx", "sy"), list(itertools.product(
    (0.4, 0.6, 0.8, 0.95), (0.4, 0.6, 0.8, 0.95), (1, -1), (1, -1))))
def test_converges_and_balances_over_an_eccentricity_grid(fx, fy, sx, sy):
    # bx/6=0.667, by/6=0.5 kern half-widths; fx, fy >= 0.4 of the half-side keeps every combo (even
    # the smallest, fx=fy=0.4 -> diamond sum 1.2) safely outside the biaxial kern, matching the
    # domain biaxial_no_tension is actually used in (biaxial() only calls it once the kern is left).
    n_kn, bx_m, by_m = 1500.0, 4.0, 3.0
    ex_m = sx * fx * bx_m / 2.0
    ey_m = sy * fy * by_m / 2.0
    solution = biaxial_no_tension(n_kn, ex_m, ey_m, bx_m, by_m)
    force, mx_first, my_first = _integrate_pressure(solution, ex_m, ey_m, bx_m, by_m, n_kn)
    assert force == pytest.approx(n_kn, rel=1e-6)
    assert mx_first == pytest.approx(n_kn * ex_m, rel=1e-6, abs=1e-6)
    assert my_first == pytest.approx(n_kn * ey_m, rel=1e-6, abs=1e-6)
    assert 0.0 < solution.compressed_ratio < 1.0
