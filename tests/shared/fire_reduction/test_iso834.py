"""ISO 834 nominal fire curve — θg(t) = 20 + 345·log10(8t+1)."""
import pytest

from strutture.shared.fire_reduction import gas_temperature_C


def test_zero_time_is_ambient():
    assert gas_temperature_C(0.0) == pytest.approx(20.0)


@pytest.mark.parametrize(
    ("t_min", "theta_C"),
    [
        (5.0, 576.41),
        (10.0, 678.427),
        (120.0, 1049.04),
    ],
)
def test_matches_cached_sheet_values(t_min, theta_C):
    assert gas_temperature_C(t_min) == pytest.approx(theta_C, rel=1e-5)


def test_monotonically_increasing():
    assert gas_temperature_C(30.0) < gas_temperature_C(60.0) < gas_temperature_C(120.0)


def test_negative_time_rejected():
    with pytest.raises(ValueError, match="t_min"):
        gas_temperature_C(-1.0)
