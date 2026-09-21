"""Fixed-behaviour tests for the rebar grade roster (NTC2018 §11.3.2)."""
import pytest

from strutture.shared.materials.rebar import fyd, rebar_properties
from strutture.shared.tables import KeyNotFound


@pytest.mark.parametrize("grado", ["B450C", "B450A"])
def test_current_ntc_grades_are_not_legacy(grado):
    assert rebar_properties(grado).legacy_grade is False


@pytest.mark.parametrize("grado", ["B500C", "FeB22k", "FeB32k", "FeB38k", "FeB44k", "RB500W"])
def test_non_ntc_grades_are_marked_legacy(grado):
    """NTC2018 §11.3.2 Tab. 11.3.Ia only admits B450C/B450A for new ordinary reinforcement."""
    assert rebar_properties(grado).legacy_grade is True


def test_fyd_default_gamma_s():
    assert rebar_properties("B450C").fyd_MPa == pytest.approx(450.0 / 1.15)
    assert fyd(450.0) == pytest.approx(450.0 / 1.15)


def test_fyd_custom_gamma_s():
    assert fyd(450.0, gamma_s=1.0) == pytest.approx(450.0)


def test_es_is_210000_mpa():
    assert rebar_properties("B450C").es_MPa == pytest.approx(210000.0)


def test_unknown_grade_raises_key_not_found():
    with pytest.raises(KeyNotFound):
        rebar_properties("B600C")
