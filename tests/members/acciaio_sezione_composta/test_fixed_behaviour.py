"""Hand-computed fixed-behaviour tests (legacy_compat=False) + boundary/validation checks."""
import math

import pytest
from pydantic import ValidationError

from strutture.members.acciaio_sezione_composta.baricentro import baricentro
from strutture.members.acciaio_sezione_composta.models import SezioneHRimpiattataInput
from strutture.members.acciaio_sezione_composta.tool import run

pytestmark = pytest.mark.unit


def _run(**overrides):
    base = {"h_profilo_mm": 114, "b_profilo_mm": 120, "tf_mm": 8, "tw_mm": 5, "piatti": ()}
    return run(SezioneHRimpiattataInput(**{**base, **overrides}))


def test_yn_bug_is_fixed_when_both_plates_are_active():
    """legacy_compat=True gets a wrong yN (H6 bug) once the second plate has area; False fixes it."""
    piatti = ({"b_mm": 10, "h_mm": 105}, {"b_mm": 10, "h_mm": 105})
    buggy = run(SezioneHRimpiattataInput(h_profilo_mm=114, b_profilo_mm=120, tf_mm=8, tw_mm=5,
                                          piatti=piatti, legacy_compat=True))
    fixed = run(SezioneHRimpiattataInput(h_profilo_mm=114, b_profilo_mm=120, tf_mm=8, tw_mm=5,
                                          piatti=piatti, legacy_compat=False))
    assert buggy.data.sezione.y_n_mm != pytest.approx(57.0, rel=1e-3)
    assert fixed.data.sezione.y_n_mm == pytest.approx(57.0, rel=1e-6)  # doubly symmetric -> yN = H/2


def test_web_height_uses_the_real_h_profilo_when_fixed():
    """legacy_compat=True ignores h_profilo_mm for the web height (hard-coded 114mm, sheet C7);
    False uses the real input."""
    buggy = _run(h_profilo_mm=200, legacy_compat=True)
    fixed = _run(h_profilo_mm=200, legacy_compat=False)
    assert buggy.data.sezione.ix_cm4 != pytest.approx(fixed.data.sezione.ix_cm4, rel=1e-3)
    # fixed: Ix of a plain doubly symmetric I-section, closed form.
    b, h, tf, tw = 120.0, 200.0, 8.0, 5.0
    ix_atteso = (b * h**3 - (b - tw) * (h - 2 * tf) ** 3) / 12.0 / 1e4
    assert fixed.data.sezione.ix_cm4 == pytest.approx(ix_atteso, rel=1e-9)


def test_bottom_flange_position_bug_is_fixed():
    """legacy_compat=True places the bottom flange centroid at plate1_b/2 instead of tf/2 (sheet
    F8); harmless only when they coincide (the default), wrong otherwise."""
    piatti = ({"b_mm": 20, "h_mm": 105},)
    buggy = run(SezioneHRimpiattataInput(h_profilo_mm=114, b_profilo_mm=120, tf_mm=8, tw_mm=5,
                                          piatti=piatti, legacy_compat=True))
    fixed = run(SezioneHRimpiattataInput(h_profilo_mm=114, b_profilo_mm=120, tf_mm=8, tw_mm=5,
                                          piatti=piatti, legacy_compat=False))
    ala_inferiore_buggy = next(e for e in buggy.data.elementi if e.nome == "Ala inferiore")
    ala_inferiore_fixed = next(e for e in fixed.data.elementi if e.nome == "Ala inferiore")
    assert ala_inferiore_buggy.y_mm == pytest.approx(10.0)  # 20/2 (plate1's own thickness)
    assert ala_inferiore_fixed.y_mm == pytest.approx(4.0)  # tf/2


def test_true_plastic_neutral_axis_differs_from_the_sheet_naive_approximation():
    """The sheet's Wpl,y approximation is 0 for an unreinforced doubly symmetric profile (it only
    sums the plates' elastic-centroid offset); the true equal-area PNA method is not."""
    legacy = _run(legacy_compat=True)
    fixed = _run(legacy_compat=False)
    assert legacy.data.sezione.wpl_y_cm3 == pytest.approx(0.0)
    assert fixed.data.sezione.wpl_y_cm3 > 0.0


def test_wpl_x_matches_closed_form_for_a_plain_doubly_symmetric_i_section():
    report = _run(legacy_compat=False)
    b, tf, tw, h = 120.0, 8.0, 5.0, 114.0
    wpl_x_atteso = 2.0 * (b * tf) * (h / 2.0 - tf / 2.0) + tw * (h / 2.0 - tf) ** 2
    assert report.data.sezione.wpl_x_cm3 == pytest.approx(wpl_x_atteso / 1e3, rel=1e-9)


def test_wpl_y_matches_closed_form_for_a_plain_doubly_symmetric_i_section():
    report = _run(legacy_compat=False)
    b, tf, tw, h = 120.0, 8.0, 5.0, 114.0
    wpl_y_atteso = 2.0 * (tf * b**2 / 4.0) + (h - 2.0 * tf) * tw**2 / 4.0
    assert report.data.sezione.wpl_y_cm3 == pytest.approx(wpl_y_atteso / 1e3, rel=1e-9)


def test_radii_of_gyration_are_sqrt_i_over_a():
    report = _run(legacy_compat=False)
    sezione = report.data.sezione
    area_cm2 = sezione.area_mm2 / 100.0
    assert sezione.raggio_x_mm == pytest.approx(math.sqrt(sezione.ix_cm4 / area_cm2) * 10.0, rel=1e-9)
    assert sezione.raggio_y_mm == pytest.approx(math.sqrt(sezione.iy_cm4 / area_cm2) * 10.0, rel=1e-9)


def test_ratio_to_unreinforced_profile_is_one_without_plates():
    report = _run(legacy_compat=False)
    assert report.data.sezione.rapporto_ix == pytest.approx(1.0, rel=1e-9)
    assert report.data.sezione.rapporto_iy == pytest.approx(1.0, rel=1e-9)


def test_ratio_to_unreinforced_profile_exceeds_one_with_plates():
    report = _run(piatti=({"b_mm": 10, "h_mm": 105},), legacy_compat=False)
    assert report.data.sezione.rapporto_ix > 1.0
    assert report.data.sezione.rapporto_iy > 1.0


def test_more_than_two_plates_alternate_sides_and_stack_outward():
    """General mode generalises beyond the sheet's 2-plate legacy layout."""
    piatti = ({"b_mm": 8, "h_mm": 105}, {"b_mm": 8, "h_mm": 105}, {"b_mm": 6, "h_mm": 60})
    report = _run(piatti=piatti, legacy_compat=False)
    nomi_x = {e.nome: e.x_mm for e in report.data.elementi if e.nome.startswith("Piatto")}
    assert nomi_x["Piatto 1"] == pytest.approx(60.0 + 4.0)  # b_profilo/2 + b/2
    assert nomi_x["Piatto 2"] == pytest.approx(-(60.0 + 4.0))
    assert nomi_x["Piatto 3"] == pytest.approx(60.0 + 8.0 + 3.0)  # stacks outward on the +x side


def test_disabled_plate_row_b_zero_contributes_nothing():
    with_zero_row = _run(piatti=({"b_mm": 0.0, "h_mm": 105},), legacy_compat=False)
    without_row = _run(piatti=(), legacy_compat=False)
    assert with_zero_row.data.sezione.area_mm2 == pytest.approx(without_row.data.sezione.area_mm2)
    assert with_zero_row.data.sezione.ix_cm4 == pytest.approx(without_row.data.sezione.ix_cm4)


def test_tf_must_leave_a_positive_web_height():
    with pytest.raises(ValidationError, match="tf_mm"):
        SezioneHRimpiattataInput(h_profilo_mm=16, b_profilo_mm=120, tf_mm=8, tw_mm=5, piatti=())


def test_legacy_compat_rejects_more_than_two_plates():
    piatti = ({"b_mm": 8, "h_mm": 105},) * 3
    with pytest.raises(ValidationError, match="legacy_compat"):
        SezioneHRimpiattataInput(h_profilo_mm=114, b_profilo_mm=120, tf_mm=8, tw_mm=5,
                                  piatti=piatti, legacy_compat=True)


def test_piatti_table_rejects_more_than_max_rows():
    piatti = ({"b_mm": 8, "h_mm": 105},) * 11
    with pytest.raises(ValidationError, match="piatti"):
        SezioneHRimpiattataInput(h_profilo_mm=114, b_profilo_mm=120, tf_mm=8, tw_mm=5, piatti=piatti)


def test_baricentro_rejects_a_section_with_no_area():
    with pytest.raises(ValueError, match="area"):
        baricentro((), legacy_compat=False)


def test_negative_plate_dimension_is_rejected():
    with pytest.raises(ValidationError):
        SezioneHRimpiattataInput(h_profilo_mm=114, b_profilo_mm=120, tf_mm=8, tw_mm=5,
                                  piatti=({"b_mm": -1.0, "h_mm": 105},))
