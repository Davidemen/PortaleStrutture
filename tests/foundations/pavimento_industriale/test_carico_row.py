"""Unit tests for `CaricoRow` (table row model, architecture-batch2.md §2)."""
import pytest
from pydantic import ValidationError

from strutture.foundations.pavimento_industriale.carico_row import CaricoRow


@pytest.mark.unit
def test_row_is_frozen() -> None:
    row = CaricoRow(caso="A", posizione="centro", p_kN=10, impronta_a_mm=100, impronta_b_mm=100, gamma=1.5, psi1=0.9)
    with pytest.raises(ValidationError):
        row.p_kN = 20  # type: ignore[misc]


@pytest.mark.unit
def test_rejects_invalid_posizione() -> None:
    with pytest.raises(ValidationError):
        CaricoRow(caso="A", posizione="centrale", p_kN=10, impronta_a_mm=100, impronta_b_mm=100, gamma=1.5, psi1=0.9)


@pytest.mark.unit
def test_gamma_and_psi1_are_per_row_columns() -> None:
    """architecture-batch2.md §7 `pavimento $L$6` fix by construction: each row carries its own
    gamma/psi1, so two rows can't accidentally share the sheet's absolute-reference bug."""
    riga_a = CaricoRow(caso="A", posizione="centro", p_kN=10, impronta_a_mm=100, impronta_b_mm=100, gamma=1.5, psi1=0.9)
    riga_b = CaricoRow(caso="B", posizione="bordo", p_kN=10, impronta_a_mm=100, impronta_b_mm=100, gamma=1.2, psi1=0.7)
    assert riga_a.gamma != riga_b.gamma
    assert riga_a.psi1 != riga_b.psi1
