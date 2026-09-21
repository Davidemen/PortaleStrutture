import pytest

from strutture.loads.vento_cpe.cpe_side import cpe_side


@pytest.mark.unit
def test_cpe_side_linear_segment():
    assert cpe_side(0.25) == pytest.approx(-0.7)


@pytest.mark.unit
def test_cpe_side_capped_segment():
    assert cpe_side(0.75) == pytest.approx(-0.9)


@pytest.mark.unit
def test_cpe_side_breakpoint_exact():
    assert cpe_side(0.5) == pytest.approx(-0.9)


@pytest.mark.unit
def test_cpe_side_not_defined_above_five():
    assert cpe_side(6.0) is None
