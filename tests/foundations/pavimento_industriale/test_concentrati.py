"""Unit tests for `concentrati` (many-rows composition, architecture-batch2.md §2: `righe` +
`inviluppo` + `governante`, checks on the envelope only -- never one check per row)."""
import pytest

from strutture.foundations.pavimento_industriale.carico_row import CaricoRow
from strutture.foundations.pavimento_industriale.concentrati import concentrati

_COMMON = {"h_mm": 200.0, "l_mm": 776.901, "fcfd_MPa": 1.45982, "fctm_MPa": 2.60682, "mrd_Nmm_m": 15046.9, "d_mm": 170.0, "v1": 0.54, "fcd_MPa": 14.1667, "v_min_MPa": 0.494975}
_CARICHI = (
    CaricoRow(caso="ruota motrice", posizione="centro", p_kN=15.5, impronta_a_mm=500, impronta_b_mm=100, gamma=1.5, psi1=0.9),
    CaricoRow(caso="ruota motrice", posizione="bordo", p_kN=15.5, impronta_a_mm=500, impronta_b_mm=100, gamma=1.5, psi1=0.9),
    CaricoRow(caso="ruota motrice", posizione="spigolo", p_kN=15.5, impronta_a_mm=500, impronta_b_mm=100, gamma=1.5, psi1=0.9),
)


@pytest.mark.unit
def test_righe_has_one_result_per_input_row_same_order() -> None:
    result, _ = concentrati(_CARICHI, **_COMMON, legacy_compat=True)
    assert [row.posizione for row in result.righe] == ["centro", "bordo", "spigolo"]


@pytest.mark.unit
def test_inviluppo_has_one_entry_per_quantity_with_governing_row() -> None:
    result, _ = concentrati(_CARICHI, **_COMMON, legacy_compat=True)
    assert len(result.inviluppo) == 5
    stress_envelope = next(row for row in result.inviluppo if row.grandezza.startswith("Tensionale"))
    assert stress_envelope.posizione == "bordo"  # bordo has the highest sigma for this footprint


@pytest.mark.unit
def test_governante_is_the_row_with_the_worst_overall_utilisation() -> None:
    result, _ = concentrati(_CARICHI, **_COMMON, legacy_compat=True)
    assert result.governante.utilizzo_max == pytest.approx(max(row.utilizzo_max for row in result.righe))


@pytest.mark.unit
def test_checks_are_on_the_envelope_only_not_per_row() -> None:
    """architecture-batch2.md §2: one check per quantity across the whole table, never per row."""
    _, checks = concentrati(_CARICHI, **_COMMON, legacy_compat=True)
    assert len(checks) == 5
    assert all(check.limit == pytest.approx(1.0) for check in checks)


@pytest.mark.unit
def test_single_row_table_matches_the_scalar_calculation() -> None:
    """Invariant (architecture-batch2.md §6): a one-row table behaves like a direct scalar call."""
    from strutture.foundations.pavimento_industriale.concentrati_riga import riga_carico

    result, _ = concentrati(_CARICHI[:1], **_COMMON, legacy_compat=True)
    direct = riga_carico(_CARICHI[0], **_COMMON, legacy_compat=True)
    assert result.righe[0] == direct
    assert result.governante == direct
