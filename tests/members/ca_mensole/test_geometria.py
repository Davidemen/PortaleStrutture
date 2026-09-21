"""Unit tests for `strutture.members.ca_mensole.geometria` (H11, H13)."""
import pytest

from strutture.members.ca_mensole.geometria import geometria
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_geometria_golden() -> None:
    result = geometria(a_mm=177, h_mm=450, c_mm=50)
    assert result.d_mm == pytest.approx(400)
    assert result.l_mm == pytest.approx(257)


@pytest.mark.unit
def test_geometria_rejects_nonpositive_effective_depth() -> None:
    with pytest.raises(CalcError):
        geometria(a_mm=100, h_mm=100, c_mm=100)


@pytest.mark.unit
def test_geometria_rejects_negative_effective_depth() -> None:
    with pytest.raises(CalcError):
        geometria(a_mm=100, h_mm=100, c_mm=150)
