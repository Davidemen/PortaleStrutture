"""Unit tests for `materiali` (concrete/steel properties, spec 'pav-fondazione-materiali' steps 1-9)."""
import pytest

from strutture.foundations.pavimento_industriale.materiali import materiali


@pytest.mark.unit
def test_materiali_matches_golden_case() -> None:
    result = materiali("C25/30", 1.5, 1.15)
    assert result.rck_MPa == pytest.approx(30.0)
    assert result.fck_MPa == pytest.approx(25.0)
    assert result.fcd_MPa == pytest.approx(14.1667, rel=1e-5)
    assert result.fcm_MPa == pytest.approx(33.0)
    assert result.fctm_MPa == pytest.approx(2.60682, rel=1e-5)
    assert result.fcfm_MPa == pytest.approx(3.12819, rel=1e-5)
    assert result.fcfk_MPa == pytest.approx(2.18973, rel=1e-5)
    assert result.fcfd_MPa == pytest.approx(1.45982, rel=1e-5)
    assert result.ecm_MPa == pytest.approx(31475.8, rel=1e-5)
    assert result.fyk_MPa == pytest.approx(450.0)
    assert result.fyd_MPa == pytest.approx(391.304, rel=1e-5)


@pytest.mark.unit
def test_fctm_uses_rck_not_fck_cnr_dt211_specific() -> None:
    """CNR-DT211/2014 fit: fctm = 0.27*Rck^(2/3), not EC2's 0.30*fck^(2/3) -- both give the same
    fctm here only because Rck != fck. Confirm the formula reads Rck, not fck."""
    result = materiali("C25/30", 1.5, 1.15)
    ec2_fctm = 0.30 * result.fck_MPa ** (2.0 / 3.0)
    assert result.fctm_MPa != pytest.approx(ec2_fctm)


@pytest.mark.unit
@pytest.mark.parametrize("gamma_c", [1.5, 1.6])
def test_gamma_c_scales_fcd_and_fcfd(gamma_c: float) -> None:
    result = materiali("C25/30", gamma_c, 1.15)
    assert result.fcd_MPa == pytest.approx(0.85 * result.fck_MPa / gamma_c, rel=1e-9)
    assert result.fcfd_MPa == pytest.approx(result.fcfk_MPa / gamma_c, rel=1e-9)
