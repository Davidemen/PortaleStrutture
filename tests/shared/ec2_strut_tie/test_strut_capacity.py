"""§6.5.2(1) strut design compressive stress: fcd (uncracked) or 0.6*nu'*fcd (cracked)."""
import pytest

from strutture.shared.ec2_strut_tie import strut_capacity


def test_uncracked_strut_uses_fcd_unreduced():
    result = strut_capacity(30.0, 1.5, cracked=False)
    assert result.sigma_rd_max_MPa == pytest.approx(30.0 / 1.5)
    assert result.fns_kN is None


def test_cracked_strut_applies_0_6_nu_prime():
    fck, gamma_c = 30.0, 1.5
    result = strut_capacity(fck, gamma_c, cracked=True)
    nu_prime = 1.0 - fck / 250.0
    assert result.sigma_rd_max_MPa == pytest.approx(0.6 * nu_prime * (fck / gamma_c))


def test_area_is_used_to_compute_force():
    result = strut_capacity(30.0, 1.5, cracked=True, area_mm2=262191.0)
    assert result.fns_kN == pytest.approx(result.sigma_rd_max_MPa * 262191.0 / 1000.0)


def test_cracked_coefficient_is_overridable():
    default = strut_capacity(30.0, 1.5, cracked=True)
    custom = strut_capacity(30.0, 1.5, cracked=True, cracked_coefficient=0.75)
    assert custom.sigma_rd_max_MPa == pytest.approx(default.sigma_rd_max_MPa * 0.75 / 0.6)


@pytest.mark.parametrize(("gamma_c", "area_mm2"), [(0.0, None), (1.5, 0.0), (1.5, -1.0)])
def test_invalid_inputs_raise(gamma_c, area_mm2):
    with pytest.raises(ValueError):
        strut_capacity(30.0, gamma_c, area_mm2=area_mm2)
