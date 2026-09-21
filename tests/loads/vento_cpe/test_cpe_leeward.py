import pytest

from strutture.loads.vento_cpe.cpe_leeward import cpe_leeward


@pytest.mark.unit
def test_cpe_leeward_first_segment():
    assert cpe_leeward(0.75) == pytest.approx(-0.45)


@pytest.mark.unit
def test_cpe_leeward_second_segment():
    assert cpe_leeward(0.6) == pytest.approx(-0.42)


@pytest.mark.unit
def test_cpe_leeward_breakpoint_exact():
    assert cpe_leeward(1.0) == pytest.approx(-0.5)


@pytest.mark.unit
def test_cpe_leeward_not_defined_above_five():
    assert cpe_leeward(5.5) is None
