"""Unit tests for `materiali` (Ac, As, fck, fcd, fyk, fyd)."""
import pytest

from strutture.foundations.travi_collegamento.materiali import materiali


@pytest.mark.unit
def test_materiali_legacy_matches_golden() -> None:
    result = materiali(400, 400, 16, 6, "C25/30", "B450C", legacy_compat=True)
    assert result.ac_mm2 == pytest.approx(160000, rel=1e-6)
    assert result.as_mm2 == pytest.approx(1206.37, rel=1e-5)
    assert result.fck_MPa == pytest.approx(24.9, rel=1e-6)
    assert result.fcd_MPa == pytest.approx(14.11, rel=1e-5)
    assert result.fyk_MPa == pytest.approx(450, rel=1e-6)
    assert result.fyd_MPa == pytest.approx(391.304, rel=1e-5)


@pytest.mark.unit
def test_materiali_code_standard_uses_ntc_literal_fck() -> None:
    """Divergence (inherited from `shared.materials.concrete.fck`, `docs/divergences/materials.md`):
    legacy_compat=False uses the NTC2018 Tab. 4.1.I literal fck (25 for C25/30), not the sheets'
    `0.83*Rck` fill-down (24.9)."""
    result = materiali(400, 400, 16, 6, "C25/30", "B450C", legacy_compat=False)
    assert result.fck_MPa == pytest.approx(25.0, rel=1e-6)
