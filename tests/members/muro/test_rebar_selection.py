"""Unit tests for `rebar_selection` (muro-sostegno rows 143-151/161-169/179-187, As.nec + callout)."""
import pytest

from strutture.members.muro import rebar_selection

pytestmark = pytest.mark.unit


def test_as_necessaria_cm2_m_matches_golden_tool4():
    """MEd=35.9317 kNm, d=0.43 m (s_base-cover), fyd=391.304 MPa -> As.nec=2.3726 cm2/m (row151)."""
    as_nec = rebar_selection.as_necessaria_cm2_m(m_ed_kNm=35.9317, d_m=0.43, fyd_MPa=391.304)
    assert as_nec == pytest.approx(2.3726, rel=1e-4)


def test_as_necessaria_cm2_m_stays_negative_for_a_favourable_moment():
    """A single combination's row can legitimately go negative (favourable MEd), same as the
    sheet's own per-row cells — see `governante_cm2_m` for the floor applied when reporting the
    design value."""
    assert rebar_selection.as_necessaria_cm2_m(m_ed_kNm=-10.0, d_m=0.43, fyd_MPa=391.304) == pytest.approx(-0.6603508597319155)


def test_governante_cm2_m_floors_a_negative_max_at_zero():
    assert rebar_selection.governante_cm2_m((-2.0, -0.5, -3.1)) == 0.0


def test_governante_cm2_m_returns_the_positive_max_untouched():
    assert rebar_selection.governante_cm2_m((-2.0, 2.3726, 0.5)) == pytest.approx(2.3726)


def test_diametro_sheet_mm_matches_golden_examples():
    assert rebar_selection.diametro_sheet_mm(2.3726, 0.2) == pytest.approx(8.0)
    assert rebar_selection.diametro_sheet_mm(0.387055, 0.2) == pytest.approx(4.0)
    assert rebar_selection.diametro_sheet_mm(2.89234, 0.2) == pytest.approx(10.0)


def test_callout_sheet_matches_golden_examples():
    assert rebar_selection.callout_sheet(2.3726, 0.2) == "1φ8/20"
    assert rebar_selection.callout_sheet(0.387055, 0.2) == "1φ4/20"
    assert rebar_selection.callout_sheet(2.89234, 0.2) == "1φ10/20"


def test_diametro_standard_mm_picks_smallest_covering_commercial_diameter():
    # area_richiesta = 0.387055*100*0.2 = 7.7411 mm2 < bar_area(6mm)=28.27mm2, so 6mm (not 4mm,
    # which is not on the EN10080 series used here) — diverges from the sheet's own 4mm.
    assert rebar_selection.diametro_standard_mm(0.387055, 0.2) == pytest.approx(6.0)
    # Tool 4/6 governing values happen to already round to a standard diameter -> no divergence.
    assert rebar_selection.diametro_standard_mm(2.3726, 0.2) == pytest.approx(8.0)
    assert rebar_selection.diametro_standard_mm(2.89234, 0.2) == pytest.approx(10.0)


def test_callout_standard_uses_shared_rebar_catalog_symbol():
    assert rebar_selection.callout_standard(0.387055, 0.2) == "1ø6/20"


def test_diametro_and_callout_dispatch_on_legacy_compat():
    assert rebar_selection.diametro_mm(0.387055, 0.2, legacy_compat=True) == pytest.approx(4.0)
    assert rebar_selection.diametro_mm(0.387055, 0.2, legacy_compat=False) == pytest.approx(6.0)
    assert rebar_selection.callout(0.387055, 0.2, legacy_compat=True) == "1φ4/20"
    assert rebar_selection.callout(0.387055, 0.2, legacy_compat=False) == "1ø6/20"
