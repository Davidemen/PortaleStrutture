import pytest

from strutture.loads.vento_cpe.hd_ratio import hd_ratio


@pytest.mark.unit
def test_hd_ratio_basic():
    assert hd_ratio(h=9, d=12) == pytest.approx(0.75)


@pytest.mark.unit
def test_hd_ratio_swapped_direction():
    assert hd_ratio(h=9, d=15) == pytest.approx(0.6)
