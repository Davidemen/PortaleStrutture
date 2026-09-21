"""§6.5.3/§9.8.1 tie rebar area As = F/fyd."""
import pytest

from strutture.shared.ec2_strut_tie import tie_area


def test_tie_area_matches_hand_computation():
    assert tie_area(f_kN=500.0, fyd_MPa=391.3) == pytest.approx(500.0 * 1000.0 / 391.3)


def test_zero_force_gives_zero_area():
    assert tie_area(0.0, 391.3) == pytest.approx(0.0)


@pytest.mark.parametrize(("f_kN", "fyd_MPa"), [(-1.0, 391.3), (100.0, 0.0), (100.0, -1.0)])
def test_invalid_inputs_raise(f_kN, fyd_MPa):
    with pytest.raises(ValueError):
        tie_area(f_kN, fyd_MPa)
