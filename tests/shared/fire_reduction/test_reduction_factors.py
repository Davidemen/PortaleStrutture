"""EN1993-1-2 Table 3.1 interpolation, both at exact tabulated rows and between brackets."""
import pytest

from strutture.shared.fire_reduction import reduction_factors
from strutture.shared.tables import KeyNotFound


@pytest.mark.parametrize(
    ("theta_C", "ky", "kp", "kE"),
    [
        (20.0, 1.0, 1.0, 1.0),
        (600.0, 0.47, 0.18, 0.31),
        (1200.0, 0.0, 0.0, 0.0),
    ],
)
def test_exact_tabulated_rows(theta_C, ky, kp, kE):
    factors = reduction_factors(theta_C)
    assert (factors.ky_theta, factors.kp_theta, factors.kE_theta) == pytest.approx((ky, kp, kE))


def test_interpolation_between_brackets_matches_cached_sheet_value():
    """acciaio-incendio!resistenza!D9/E9, θ=576.41 -> Kfy=0.543128, KE=0.37841 (t=5min row)."""
    factors = reduction_factors(576.41)
    assert factors.ky_theta == pytest.approx(0.543128, rel=1e-5)
    assert factors.kE_theta == pytest.approx(0.378410, rel=1e-5)


def test_below_table_range_raises():
    with pytest.raises(KeyNotFound):
        reduction_factors(10.0)


def test_above_table_range_raises():
    with pytest.raises(KeyNotFound):
        reduction_factors(1300.0)
