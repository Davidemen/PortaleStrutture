import pytest

from strutture.members.ca_travi.materiali import materiali_trave


@pytest.mark.unit
def test_materiali_trave_reuses_shared_concrete_and_rebar_properties():
    out = materiali_trave("C35/45", "RB500W", legacy_compat=True)
    assert out.calcestruzzo.classe == "C35/45"
    assert out.calcestruzzo.fck_MPa == pytest.approx(37.35)  # legacy fill-down fck=0.83*Rck
    assert out.calcestruzzo.fcd_MPa == pytest.approx(21.165, rel=1e-6)
    assert out.acciaio.grado == "RB500W"
    assert out.acciaio.fyd_MPa == pytest.approx(434.782608696, rel=1e-6)


@pytest.mark.unit
def test_materiali_trave_fixed_mode_uses_literal_fck():
    out = materiali_trave("C35/45", "B450C", legacy_compat=False)
    assert out.calcestruzzo.fck_MPa == pytest.approx(35.0)
    assert out.acciaio.fyd_MPa == pytest.approx(450.0 / 1.15, rel=1e-6)
