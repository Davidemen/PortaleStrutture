import pytest

from strutture.loads.vento_cpe.cpe_windward import cpe_windward


@pytest.mark.unit
def test_cpe_windward_linear_segment():
    assert cpe_windward(0.75) == pytest.approx(0.775)


@pytest.mark.unit
def test_cpe_windward_at_zero():
    assert cpe_windward(0.0) == pytest.approx(0.7)


@pytest.mark.unit
def test_cpe_windward_capped_segment():
    assert cpe_windward(3.0) == pytest.approx(0.8)


@pytest.mark.unit
def test_cpe_windward_breakpoint_exact():
    assert cpe_windward(1.0) == pytest.approx(0.8)


@pytest.mark.unit
def test_cpe_windward_not_defined_above_five():
    assert cpe_windward(5.01) is None


@pytest.mark.unit
def test_cpe_windward_defined_at_five():
    assert cpe_windward(5.0) == pytest.approx(0.8)
