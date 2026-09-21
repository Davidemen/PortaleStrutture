"""Unit tests for `sismica_en` — spectrum-type selection and the S-column-selection sheet bug."""
import pytest

from strutture.foundations.travi_collegamento.sismica_en import sismica_en


@pytest.mark.unit
def test_sismica_en_golden_tipo2_legacy_matches_sheet() -> None:
    """Ms=5.6 (>5.5) -> label TIPO2, but the sheet bug picks the "S Tipo 1" column value (1.2 for
    soil B) rather than "S Tipo 2" (1.35) — legacy_compat=True reproduces this."""
    result = sismica_en("B", 5.6, 0.151, legacy_compat=True)
    assert result.tipo_spettro == "TIPO2"
    assert result.s == pytest.approx(1.2)
    assert result.amax_g == pytest.approx(0.1812, rel=1e-4)


@pytest.mark.unit
def test_sismica_en_fixed_aligns_column_with_label() -> None:
    """legacy_compat=False, EN1998-1 §3.2.2.2(2)P: Ms=5.6 > 5.5 -> Tipo 1 (label TIPO1), which
    correctly picks the "S Tipo 1" column (1.2 for soil B)."""
    result = sismica_en("B", 5.6, 0.151, legacy_compat=False)
    assert result.tipo_spettro == "TIPO1"
    assert result.s == pytest.approx(1.2)


@pytest.mark.unit
def test_sismica_en_ground_d_low_ms_uses_type2_spectrum() -> None:
    """EN1998-1 §3.2.2.2(2)P: Ms=5.0 <= 5.5 -> Tipo 2 spectrum (higher S). Ground D: S=1.8, not
    the inverted-rule 1.35 (regression for the CRITICAL spectrum-type finding)."""
    result = sismica_en("D", 5.0, 0.151, legacy_compat=False)
    assert result.tipo_spettro == "TIPO2"
    assert result.s == pytest.approx(1.8)


@pytest.mark.unit
def test_sismica_en_tipo2_boundary_inclusive() -> None:
    """Ms=5.5 is "not greater than 5.5" -> Tipo 2 (boundary inclusive)."""
    result = sismica_en("B", 5.5, 0.151, legacy_compat=False)
    assert result.tipo_spettro == "TIPO2"


@pytest.mark.unit
def test_sismica_en_legacy_and_fixed_give_same_s() -> None:
    """The sheet's C8 column selection (`Tabelle!M131:O134`, `IF(C6<=5.5,3,2)`) was already
    EN-correct; only its own C7 label (`IF(C6<=5.5,"TIPO1","TIPO2")`) was inverted relative to
    EN1998-1 §3.2.2.2(2)P. So S must be identical under both flags -- only `tipo_spettro`
    (the reported label) differs."""
    legacy = sismica_en("D", 5.0, 0.151, legacy_compat=True)
    fixed = sismica_en("D", 5.0, 0.151, legacy_compat=False)
    assert legacy.s == pytest.approx(fixed.s) == pytest.approx(1.8)
    assert legacy.tipo_spettro == "TIPO1"  # sheet's mislabeled C7
    assert fixed.tipo_spettro == "TIPO2"  # EN-correct label


@pytest.mark.unit
def test_sismica_en_soil_a_alpha_zero() -> None:
    """EN1998-5 §5.4.1.2 point 5 -- tie beams not required for ground type A -> α=0."""
    result = sismica_en("A", 5.6, 0.151, legacy_compat=False)
    assert result.alpha == pytest.approx(0.0)
