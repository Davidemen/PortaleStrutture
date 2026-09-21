import pytest

from strutture.loads.sisma.smorzamento import ETA_MIN, smorzamento_eta


@pytest.mark.unit
def test_eta_at_5_percent_damping_is_one():
    assert smorzamento_eta(5) == pytest.approx(1.0, rel=1e-9)


@pytest.mark.unit
def test_eta_decreases_as_damping_increases():
    assert smorzamento_eta(10) < smorzamento_eta(5) < smorzamento_eta(2)


@pytest.mark.unit
def test_eta_is_floored_at_0_55_for_high_damping():
    """NTC2018 eq. 3.2.6: eta = sqrt(10/(5+xi)) >= 0.55. Unfloored, xi=28.06% already gives eta<0.55."""
    unfloored_would_be = (10.0 / (5.0 + 40.0)) ** 0.5
    assert unfloored_would_be < ETA_MIN
    assert smorzamento_eta(40) == pytest.approx(ETA_MIN, rel=1e-9)


@pytest.mark.unit
def test_eta_floor_is_a_named_constant():
    assert ETA_MIN == pytest.approx(0.55)
