import pytest

from strutture.foundations.plinti_isolati.materiali import materiali


@pytest.mark.golden
def test_materiali_golden_legacy() -> None:
    """docs/specs/fond-plinti-isolati.md golden case: fyd=434.783, fck=37.35, fctm=3.35208 N/mm2."""
    result = materiali("C35/45", "B500C", 1.15, legacy_compat=True)
    assert result.acciaio.fyd_MPa == pytest.approx(434.783, rel=1e-5)
    assert result.calcestruzzo.fck_MPa == pytest.approx(37.35, rel=1e-6)
    assert result.calcestruzzo.fctm_MPa == pytest.approx(3.35208, rel=1e-5)


@pytest.mark.unit
def test_materiali_fck_fix_ntc2018_literal() -> None:
    """Divergence (shared `materials.concrete`, merge C1): non-legacy fck is the NTC2018 Tab. 4.1.I
    literal value (35 for C35/45), not the sheet's `0.83*Rck` fill-down (37.35)."""
    result = materiali("C35/45", "B500C", 1.15, legacy_compat=False)
    assert result.calcestruzzo.fck_MPa == pytest.approx(35.0)
