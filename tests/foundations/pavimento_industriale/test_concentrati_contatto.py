"""Unit tests for `contatto` (Westergaard equivalent contact radius, spec steps 1-2)."""
import math

import pytest

from strutture.foundations.pavimento_industriale.concentrati_contatto import contatto


@pytest.mark.unit
def test_contatto_matches_golden_case() -> None:
    result = contatto(500, 100, 200)
    assert result.ac_mm2 == pytest.approx(50000.0)
    assert result.rr_mm == pytest.approx(126.157, rel=1e-5)
    assert result.b_mm == pytest.approx(120.861, rel=1e-5)


@pytest.mark.unit
def test_no_correction_when_rr_over_h_exceeds_threshold() -> None:
    """rr/h >= 1.724 -> b = rr (no Westergaard correction)."""
    result = contatto(1000, 1000, 100)
    assert result.rr_mm / 100.0 >= 1.724
    assert result.b_mm == pytest.approx(result.rr_mm)


@pytest.mark.unit
def test_correction_applied_below_threshold() -> None:
    result = contatto(500, 100, 200)
    assert result.rr_mm / 200.0 < 1.724
    expected_b = math.sqrt(1.6 * result.rr_mm**2 + 200.0**2) - 0.675 * 200.0
    assert result.b_mm == pytest.approx(expected_b)
