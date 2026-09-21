"""Unit tests for `strutture.members.ca_mensole.capacita` (H28, H30-H33, divergence H30)."""
import math

import pytest

from strutture.members.ca_mensole.capacita import capacita, coefficiente_c


@pytest.mark.unit
def test_coefficiente_c_no_stirrups() -> None:
    """Divergence: H30 reimplemented as a plain number (sheet returns the string "1" implicitly
    coerced); no numeric difference from the sheet."""
    assert coefficiente_c("NO") == 1.0
    assert isinstance(coefficiente_c("NO"), float)


@pytest.mark.unit
def test_coefficiente_c_with_vertical_stirrups() -> None:
    """Divergence: H30 returns the string "1.5" on the sheet's SI branch; here it is a float."""
    assert coefficiente_c("SI") == 1.5
    assert isinstance(coefficiente_c("SI"), float)


@pytest.mark.unit
def test_capacita_golden() -> None:
    result = capacita(
        as_hor_mm2=904.779, as_incl_mm2=0, fyd_MPa=391.304347826087, hed_kN=0,
        d_mm=400, l_mm=257, b_mm=800, fcd_MPa=18.8133333333333, c_coeff=1.0, angolo_incl_deg=0,
    )
    assert result.prs_kN == pytest.approx(495.937, rel=1e-5)
    assert result.prc_kN == pytest.approx(1595.16, rel=1e-5)
    assert result.dpr_kN == pytest.approx(0, abs=1e-9)
    assert result.pr_kN == pytest.approx(495.937, rel=1e-5)


@pytest.mark.unit
def test_capacita_hed_reduces_prs() -> None:
    baseline = capacita(
        as_hor_mm2=904.779, as_incl_mm2=0, fyd_MPa=391.304347826087, hed_kN=0,
        d_mm=400, l_mm=257, b_mm=800, fcd_MPa=18.8133333333333, c_coeff=1.0, angolo_incl_deg=0,
    )
    with_hed = capacita(
        as_hor_mm2=904.779, as_incl_mm2=0, fyd_MPa=391.304347826087, hed_kN=50,
        d_mm=400, l_mm=257, b_mm=800, fcd_MPa=18.8133333333333, c_coeff=1.0, angolo_incl_deg=0,
    )
    assert with_hed.prs_kN < baseline.prs_kN


@pytest.mark.unit
def test_capacita_inclined_bars_contribute_reduced_dpr() -> None:
    result = capacita(
        as_hor_mm2=904.779, as_incl_mm2=314.159265358979, fyd_MPa=391.304347826087, hed_kN=0,
        d_mm=400, l_mm=257, b_mm=800, fcd_MPa=18.8133333333333, c_coeff=1.0, angolo_incl_deg=45,
    )
    expected_dpr = 314.159265358979 * 391.304347826087 * math.sin(math.radians(45)) / 1000
    assert result.dpr_kN == pytest.approx(expected_dpr, rel=1e-6)
    assert result.pr_kN == pytest.approx(result.prs_kN + 0.8 * result.dpr_kN, rel=1e-9)


@pytest.mark.unit
def test_capacita_vertical_stirrups_scale_prc() -> None:
    without = capacita(
        as_hor_mm2=904.779, as_incl_mm2=0, fyd_MPa=391.304347826087, hed_kN=0,
        d_mm=400, l_mm=257, b_mm=800, fcd_MPa=18.8133333333333, c_coeff=1.0, angolo_incl_deg=0,
    )
    with_stirrups = capacita(
        as_hor_mm2=904.779, as_incl_mm2=0, fyd_MPa=391.304347826087, hed_kN=0,
        d_mm=400, l_mm=257, b_mm=800, fcd_MPa=18.8133333333333, c_coeff=1.5, angolo_incl_deg=0,
    )
    assert with_stirrups.prc_kN == pytest.approx(1.5 * without.prc_kN, rel=1e-9)
