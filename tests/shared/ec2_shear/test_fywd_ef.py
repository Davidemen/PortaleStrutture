"""§6.4.5(1) eq. 6.52 effective yield strength of punching reinforcement, capped at fywd
(fixes architecture-batch2.md §7 `punzonamento H56`, uncapped in the sheet)."""
import pytest

from strutture.shared.ec2_shear import fywd_ef


def test_below_cap_uses_the_linear_formula():
    d_mm = 430.0
    assert fywd_ef(d_mm, fywd_MPa=391.3) == pytest.approx(250.0 + 0.25 * d_mm)


def test_thick_slab_is_capped_at_fywd():
    """d>=564mm makes 250+0.25d exceed a typical fywd=391.3 MPa (B450C, gamma_s=1.15)."""
    d_mm = 600.0
    assert fywd_ef(d_mm, fywd_MPa=391.3) == pytest.approx(391.3)


@pytest.mark.parametrize(("d_mm", "fywd_MPa"), [(0.0, 391.3), (-10.0, 391.3), (430.0, 0.0), (430.0, -5.0)])
def test_invalid_inputs_raise(d_mm, fywd_MPa):
    with pytest.raises(ValueError):
        fywd_ef(d_mm, fywd_MPa)
