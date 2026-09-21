import pytest

from strutture.loads.sisma.fattore_struttura_q import fattore_struttura_q


@pytest.mark.unit
def test_q_equals_q0_times_kr_for_uls():
    assert fattore_struttura_q(1.5, 1.0, is_uls=True) == pytest.approx(1.5)
    assert fattore_struttura_q(1.5, 0.8, is_uls=True) == pytest.approx(1.2)


@pytest.mark.unit
def test_q_is_one_for_sle():
    assert fattore_struttura_q(1.5, 0.8, is_uls=False) == pytest.approx(1.0)
