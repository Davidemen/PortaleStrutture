import pytest

from strutture.shared.footing_pressure.navier import biaxial_navier

pytestmark = pytest.mark.unit


def test_zero_eccentricity_gives_uniform_corners():
    result = biaxial_navier(n_kn=1000.0, ex_m=0.0, ey_m=0.0, bx_m=4.0, by_m=5.0)
    uniform = 1000.0 / (4.0 * 5.0)
    assert result.corners_kpa == pytest.approx((uniform,) * 4)
    assert result.sigma_max_kpa == pytest.approx(uniform)
    assert result.sigma_min_kpa == pytest.approx(uniform)
    assert result.compressed_ratio == 1.0
    assert result.neutral_axis is None


def test_reduces_to_uniaxial_when_one_eccentricity_is_zero():
    n_kn, bx_m, by_m, ex_m = 1000.0, 4.0, 5.0, 0.3
    result = biaxial_navier(n_kn=n_kn, ex_m=ex_m, ey_m=0.0, bx_m=bx_m, by_m=by_m)
    uniform = n_kn / (bx_m * by_m)
    expected_max = uniform * (1.0 + 6.0 * ex_m / bx_m)
    expected_min = uniform * (1.0 - 6.0 * ex_m / bx_m)
    assert result.sigma_max_kpa == pytest.approx(expected_max)
    assert result.sigma_min_kpa == pytest.approx(expected_min)


def test_kern_boundary_corner_is_exactly_zero():
    bx_m, by_m = 4.0, 4.0
    ex_m, ey_m = bx_m / 12.0, by_m / 12.0  # ex/(bx/6) + ey/(by/6) = 0.5+0.5 = 1
    result = biaxial_navier(n_kn=1000.0, ex_m=ex_m, ey_m=ey_m, bx_m=bx_m, by_m=by_m)
    assert result.sigma_min_kpa == pytest.approx(0.0, abs=1e-9)
    assert result.in_kern is True


def test_swap_x_and_y_gives_the_same_pressures():
    n_kn, bx_m, by_m, ex_m, ey_m = 900.0, 4.0, 6.0, 0.4, 0.2
    result = biaxial_navier(n_kn=n_kn, ex_m=ex_m, ey_m=ey_m, bx_m=bx_m, by_m=by_m)
    swapped = biaxial_navier(n_kn=n_kn, ex_m=ey_m, ey_m=ex_m, bx_m=by_m, by_m=bx_m)
    assert swapped.sigma_max_kpa == pytest.approx(result.sigma_max_kpa)
    assert swapped.sigma_min_kpa == pytest.approx(result.sigma_min_kpa)
    assert sorted(swapped.corners_kpa) == pytest.approx(sorted(result.corners_kpa))


def test_equilibrium_corner_average_style_force_matches_n():
    # For a bilinear plane over a rectangle, the mean of the 4 corner pressures times the area
    # equals the total force (exact for any bilinear/linear field over a rectangle).
    n_kn, bx_m, by_m, ex_m, ey_m = 1234.0, 3.0, 5.0, 0.1, 0.15  # inside the kern: 0.1/0.5+0.15/0.833 = 0.38
    result = biaxial_navier(n_kn=n_kn, ex_m=ex_m, ey_m=ey_m, bx_m=bx_m, by_m=by_m)
    mean_corner = sum(result.corners_kpa) / 4.0
    assert mean_corner * bx_m * by_m == pytest.approx(n_kn, rel=1e-9)
