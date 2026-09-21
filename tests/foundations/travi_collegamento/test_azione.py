"""Unit tests for `azione` (Nsd, NEd)."""
import pytest

from strutture.foundations.travi_collegamento.azione import azione


@pytest.mark.unit
def test_azione_golden() -> None:
    result = azione(2000, 2500, 0.1812, 0.3)
    assert result.nsd_kN == pytest.approx(2250)
    assert result.ned_kN == pytest.approx(122.31, rel=1e-5)


@pytest.mark.unit
def test_azione_zero_alpha_gives_zero_ned() -> None:
    result = azione(2000, 2500, 0.1812, 0.0)
    assert result.ned_kN == 0.0
