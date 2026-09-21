"""instabilita_flessionale.py — flexural buckling reduction factors (column-check!W23-W32)."""
import pytest

from strutture.members.acciaio_colonna_ec3.instabilita_flessionale import (
    costruisci_instabilita_flessionale,
    fattore_chi,
    fattore_phi,
    snellezza_adimensionale,
)


@pytest.mark.unit
def test_snellezza_adimensionale() -> None:
    assert snellezza_adimensionale(10528, 345, 3531.51) == pytest.approx(1.01415, rel=1e-4)


@pytest.mark.unit
def test_fattore_phi_and_chi_golden_values() -> None:
    phi = fattore_phi(0.34, 1.01415)
    assert phi == pytest.approx(1.15266, rel=1e-4)
    assert fattore_chi(phi, 1.01415) == pytest.approx(0.588068, rel=1e-4)


@pytest.mark.unit
def test_chi_capped_at_one_for_low_slenderness() -> None:
    phi = fattore_phi(0.21, 0.1)
    assert fattore_chi(phi, 0.1) == 1.0


@pytest.mark.unit
def test_costruisci_instabilita_flessionale_picks_max_slenderness() -> None:
    result = costruisci_instabilita_flessionale(
        area_mm2=10528, fyd_MPa=345, fyk_MPa=345, ncr_y_kN=3531.51, ncr_z_kN=20580.2, ncr_t_kN=34315.3,
        alpha_yy=0.34, alpha_zz=0.49, legacy_compat=True,
    )
    assert result.lambda_max == pytest.approx(result.lambda_yy)
    assert result.chi_yy == pytest.approx(0.588068, rel=1e-4)
    assert result.chi_zz == pytest.approx(0.886636, rel=1e-4)


@pytest.mark.unit
def test_fixed_mode_uses_fyk_not_fyd_for_lambda_bar() -> None:
    """EN1993-1-1 eq. (6.50): lambda_bar = sqrt(A*fy/Ncr) on the characteristic fy, gammaM0 excluded."""
    fyk = 345.0
    fyd = fyk / 1.05
    legacy = costruisci_instabilita_flessionale(
        area_mm2=10528, fyd_MPa=fyd, fyk_MPa=fyk, ncr_y_kN=3531.51, ncr_z_kN=20580.2, ncr_t_kN=34315.3,
        alpha_yy=0.34, alpha_zz=0.49, legacy_compat=True,
    )
    fixed = costruisci_instabilita_flessionale(
        area_mm2=10528, fyd_MPa=fyd, fyk_MPa=fyk, ncr_y_kN=3531.51, ncr_z_kN=20580.2, ncr_t_kN=34315.3,
        alpha_yy=0.34, alpha_zz=0.49, legacy_compat=False,
    )
    assert legacy.lambda_yy == pytest.approx(snellezza_adimensionale(10528, fyd, 3531.51))
    assert fixed.lambda_yy == pytest.approx(snellezza_adimensionale(10528, fyk, 3531.51))
    assert fixed.lambda_yy > legacy.lambda_yy  # fyk > fyd -> lambda_bar increases, chi decreases (non-conservative fix removed)
    assert fixed.chi_yy < legacy.chi_yy
