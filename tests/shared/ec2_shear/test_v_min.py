"""§6.2.2(1) eq. 6.3N minimum shear resistance."""
import pytest

from strutture.shared.ec2_shear import k_size, v_min


def test_v_min_matches_hand_computation():
    k = 1.5
    fck = 30.0
    assert v_min(k, fck) == pytest.approx(0.035 * 1.5**1.5 * 30.0**0.5, rel=1e-9)


def test_v_min_custom_national_annex_coefficient():
    assert v_min(1.5, 30.0, coefficient=0.05) == pytest.approx(0.05 * 1.5**1.5 * 30.0**0.5, rel=1e-9)


def test_v_min_uses_k_size_helper():
    k = k_size(300.0)
    assert v_min(k, 25.0) > 0


@pytest.mark.parametrize(("k", "fck_MPa"), [(0.0, 30.0), (-1.0, 30.0), (1.0, 0.0), (1.0, -5.0)])
def test_v_min_rejects_non_positive_inputs(k, fck_MPa):
    with pytest.raises(ValueError):
        v_min(k, fck_MPa)
