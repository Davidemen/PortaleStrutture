"""Unit tests for `sottofondo` (Winkler subgrade + plate stiffness, spec steps 10-17)."""
import pytest

from strutture.foundations.pavimento_industriale.sottofondo import sottofondo

_ECM_MPA = 31475.8
_FCK_MPA = 25.0


@pytest.mark.unit
def test_sottofondo_matches_golden_case_lookup() -> None:
    result = sottofondo(200, 30, 0.2, _ECM_MPA, _FCK_MPA, sottofondo_tipo="materiale di riporto costipato", kt_manuale_N_mm3=None)
    assert result.kt_N_mm3 == pytest.approx(0.06)
    assert result.d_mm == pytest.approx(170.0)
    assert result.lambda_mm1 == pytest.approx(0.000919499, rel=1e-5)
    assert result.w_mm3_m == pytest.approx(6.66667e6, rel=1e-5)
    assert result.l_mm == pytest.approx(776.901, rel=1e-5)
    assert result.k_ec2 == pytest.approx(2.0)
    assert result.v_min_MPa == pytest.approx(0.494975, rel=1e-5)
    assert result.v1 == pytest.approx(0.54, rel=1e-5)


@pytest.mark.unit
def test_sottofondo_manual_override_bypasses_lookup() -> None:
    result = sottofondo(200, 30, 0.2, _ECM_MPA, _FCK_MPA, sottofondo_tipo=None, kt_manuale_N_mm3=0.06)
    assert result.kt_N_mm3 == pytest.approx(0.06)


@pytest.mark.unit
def test_sottofondo_requires_exactly_one_source() -> None:
    with pytest.raises(ValueError, match="sottofondo_tipo"):
        sottofondo(200, 30, 0.2, _ECM_MPA, _FCK_MPA, sottofondo_tipo=None, kt_manuale_N_mm3=None)


@pytest.mark.unit
def test_k_ec2_clamped_at_two_for_thin_slabs() -> None:
    """d << 200mm would push sqrt(200/d) past 1, but k is clamped at 2 (EC2 §6.2.2(1))."""
    result = sottofondo(60, 10, 0.2, _ECM_MPA, _FCK_MPA, sottofondo_tipo="soffice", kt_manuale_N_mm3=None)
    assert result.k_ec2 == pytest.approx(2.0)
