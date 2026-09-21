"""Unit tests for `trazione` — including the sheet's "check against T.L._c instead of NEd" bug."""
import pytest

from strutture.foundations.travi_collegamento.trazione import trazione


@pytest.mark.unit
def test_trazione_golden_passes_both_modes() -> None:
    result_fixed = trazione(1206.37, 391.304, 122.31, 0.054177, legacy_compat=False)
    assert result_fixed.ntrd_kN == pytest.approx(472.058, rel=1e-5)
    assert result_fixed.verifica.passed
    assert result_fixed.tasso_lavoro == pytest.approx(0.259099, rel=1e-4)

    result_legacy = trazione(1206.37, 391.304, 122.31, 0.054177, legacy_compat=True)
    assert result_legacy.verifica.passed


@pytest.mark.unit
def test_trazione_fixed_catches_undersized_reinforcement() -> None:
    """Small As (φ8, 2 bars) with a realistic NEd: the fixed comparison (Nt,Rd vs NEd) fails."""
    ned_kN, ntrd_kN = 339.75, 39.33
    result = trazione(100.53, 391.304, ned_kN, tasso_lavoro_compressione=0.05, legacy_compat=False)
    assert result.ntrd_kN == pytest.approx(ntrd_kN, rel=1e-3)
    assert not result.verifica.passed


@pytest.mark.unit
def test_trazione_legacy_bug_still_passes_when_capacity_is_tiny() -> None:
    """Sheet bug: the legacy comparison is against the compression work ratio (~0-1), so it stays
    "OK" even though Nt,Rd (39.33 kN) is far below the real demand NEd (339.75 kN)."""
    result = trazione(100.53, 391.304, 339.75, tasso_lavoro_compressione=0.05, legacy_compat=True)
    assert result.verifica.passed
