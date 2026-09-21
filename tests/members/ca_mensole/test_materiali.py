"""Unit tests for `strutture.members.ca_mensole.materiali` (Z5-Z9, fixed-behaviour + divergences)."""
import pytest

from strutture.members.ca_mensole.materiali import materiali
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_materiali_b450c_c32_40_legacy() -> None:
    """Reproduces the sheet's fck fill-down bug (0.83*Rck) under legacy_compat=True (golden §8)."""
    result = materiali("B450C", "C32/40", legacy_compat=True)
    assert result.gamma_s == pytest.approx(1.15)
    assert result.gamma_c == pytest.approx(1.5)
    assert result.fyd_MPa == pytest.approx(391.304347826087, rel=1e-9)
    assert result.fcd_MPa == pytest.approx(18.8133333333333, rel=1e-9)


@pytest.mark.unit
def test_materiali_fcd_divergence_legacy_vs_code_standard() -> None:
    """Divergence: legacy_compat=False uses the NTC2018 literal fck=32, not the sheet's fill-down
    33.2 (docs/divergences/ca-mensole.md)."""
    fixed = materiali("B450C", "C32/40", legacy_compat=False)
    assert fixed.fcd_MPa == pytest.approx(0.85 * 32 / 1.5, rel=1e-9)
    assert fixed.fcd_MPa != pytest.approx(18.8133333333333, rel=1e-6)


@pytest.mark.unit
def test_materiali_feb22k_legacy_raises() -> None:
    """Divergence: FeB22k is selectable via H14 but absent from Tabelle!M45:P49 -> #N/A on the
    real sheet; legacy_compat=True reproduces the crash."""
    with pytest.raises(CalcError):
        materiali("FeB22k", "C32/40", legacy_compat=True)


@pytest.mark.unit
def test_materiali_feb22k_code_standard_fixed() -> None:
    """legacy_compat=False fixes the missing-row bug via the shared union rebar table."""
    result = materiali("FeB22k", "C32/40", legacy_compat=False)
    assert result.fyd_MPa == pytest.approx(215.0 / 1.15, rel=1e-9)
