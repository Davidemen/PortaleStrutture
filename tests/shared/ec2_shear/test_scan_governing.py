"""Exhaustive scan replacing the spreadsheet fill-down + MAX/VLOOKUP idiom
(docs/specs/ca-punzonamento.md step 5: 151 samples of a/d in [0.5, 2.0])."""
import pytest

from strutture.shared.ec2_shear import scan_governing


def test_monotonic_function_degenerates_to_upper_bound():
    """Matches the golden case: the ratio is monotonically increasing, so x* = 2.0 (151 samples)."""
    result = scan_governing(lambda x: x, lo=0.5, hi=2.0, step=0.01)
    assert result.x == pytest.approx(2.0)
    assert result.index == 150


def test_interior_maximum_is_found():
    result = scan_governing(lambda x: -((x - 1.3) ** 2) + 10.0, lo=0.5, hi=2.0, step=0.01)
    assert result.x == pytest.approx(1.3, abs=1e-9)
    assert result.value == pytest.approx(10.0)


def test_single_sample_when_lo_equals_hi():
    result = scan_governing(lambda x: x, lo=1.0, hi=1.0, step=0.1)
    assert result.x == pytest.approx(1.0)
    assert result.index == 0


@pytest.mark.parametrize(("lo", "hi", "step"), [(0.5, 2.0, 0.0), (0.5, 2.0, -0.1), (2.0, 0.5, 0.1)])
def test_invalid_range_raises(lo, hi, step):
    with pytest.raises(ValueError):
        scan_governing(lambda x: x, lo, hi, step)
