"""Unit tests for `armatura` (mesh reinforcement area + capacity, spec steps 10-11/12)."""
import pytest

from strutture.foundations.pavimento_industriale.armatura import armatura


@pytest.mark.unit
def test_armatura_matches_golden_case() -> None:
    result = armatura(8, 200, 170, 391.304)
    assert result.as_mm2_m == pytest.approx(251.327, rel=1e-5)
    assert result.mrd_Nmm_m == pytest.approx(15046.9, rel=1e-5)


@pytest.mark.unit
def test_armatura_scales_with_diameter_squared() -> None:
    small = armatura(6, 200, 170, 391.304)
    large = armatura(12, 200, 170, 391.304)
    assert large.as_mm2_m == pytest.approx(small.as_mm2_m * 4, rel=1e-9)
