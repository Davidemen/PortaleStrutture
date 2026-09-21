import pytest

from strutture.foundations.plinti_pali.materiali import materiali


@pytest.mark.unit
def test_materiali_fck_e_letterale_indipendente_dal_legacy_compat_del_plinto() -> None:
    """The pile-cap sheet takes `fck` as a plain literal (`AG7 f'c = fck = 32`), not derived from a
    cube strength Rck via a class table: `classe_calcestruzzo` must always resolve to the class's
    own literal fck (docs/divergences/plinti-pali.md), regardless of this tool's own `legacy_compat`
    (which only reproduces `Footing check`'s own bugs, unrelated to that other workbook's quirk)."""
    result = materiali("C32/40", "B450C", 1.15)
    assert result.calcestruzzo.fck_MPa == pytest.approx(32.0, rel=1e-9)
    assert result.acciaio.fyd_MPa == pytest.approx(450.0 / 1.15, rel=1e-9)
