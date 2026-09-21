"""§6.4.5(3) maximum punching stress at u0. The coefficient in front of nu*fcd is a national-annex
parameter (exposed as a keyword, see module docstring) — this test only pins the formula shape, not a
specific NA value; the sheet's own (different, simplified) coefficient stays inside `ca_punzonamento`."""
import pytest

from strutture.shared.ec2_shear import v_rd_max
from strutture.shared.ec2_shear.v_rd_max import (
    V_RD_MAX_COEFF_2004_NA_IT,
    V_RD_MAX_COEFF_A1_2014,
    V_RD_MAX_COEFFICIENT_EN,
)


def test_v_rd_max_matches_hand_computation():
    """The function default is `V_RD_MAX_COEFF_A1_2014` (0.4, EN 1992-1-1:2004/A1:2014 §6.4.5(3),
    the more conservative of the two disputed values): vRd,max = 0.4*nu*fcd, fcd = alpha_cc*fck/gamma_c
    with alpha_cc = NTC2018 default (0.85), both overridable keywords."""
    result = v_rd_max(fck_MPa=35.0, gamma_c=1.5)
    nu = 0.6 * (1.0 - 35.0 / 250.0)
    fcd = 0.85 * 35.0 / 1.5
    assert result.nu == pytest.approx(nu)
    assert result.fcd_MPa == pytest.approx(fcd)
    assert result.v_rd_max_MPa == pytest.approx(V_RD_MAX_COEFF_A1_2014 * nu * fcd)


def test_coefficient_is_overridable_for_national_annex():
    """`V_RD_MAX_COEFF_2004_NA_IT` (0.5, EN 1992-1-1:2004 + Appendice Nazionale italiana 2013) is the
    other named, explicit choice — never silently mixed with the default."""
    a1_2014_default = v_rd_max(fck_MPa=35.0)
    na_it = v_rd_max(fck_MPa=35.0, coefficient=V_RD_MAX_COEFF_2004_NA_IT)
    assert na_it.v_rd_max_MPa == pytest.approx(
        a1_2014_default.v_rd_max_MPa * V_RD_MAX_COEFF_2004_NA_IT / V_RD_MAX_COEFF_A1_2014,
    )


def test_deprecated_alias_matches_a1_2014_constant():
    """`V_RD_MAX_COEFFICIENT_EN` is a deprecated alias kept only for existing importers."""
    assert V_RD_MAX_COEFFICIENT_EN == pytest.approx(V_RD_MAX_COEFF_A1_2014)


def test_alpha_cc_defaults_to_ntc2018_value():
    from strutture.shared.materials.concrete import ALPHA_CC

    assert ALPHA_CC == pytest.approx(0.85)
    result = v_rd_max(fck_MPa=35.0)
    assert result.fcd_MPa == pytest.approx(ALPHA_CC * 35.0 / 1.5)


def test_alpha_cc_is_overridable():
    result = v_rd_max(fck_MPa=35.0, alpha_cc=1.0)
    assert result.fcd_MPa == pytest.approx(35.0 / 1.5)


@pytest.mark.parametrize(("fck_MPa", "gamma_c"), [(0.0, 1.5), (-10.0, 1.5), (30.0, 0.0)])
def test_invalid_inputs_raise(fck_MPa, gamma_c):
    with pytest.raises(ValueError):
        v_rd_max(fck_MPa, gamma_c)
