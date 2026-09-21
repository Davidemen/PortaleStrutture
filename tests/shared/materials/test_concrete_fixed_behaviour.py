"""Fixed-behaviour tests (legacy_compat=False): NTC2018 formula checks and the C35/45 divergence
(docs/divergences/materials.md)."""
import pytest

from strutture.shared.materials.concrete import (
    ConcreteClass,
    concrete_properties,
    ecm,
    fcd,
    fck,
    fcm,
    fctd,
    fctk,
    fctm,
)
from strutture.shared.tables import KeyNotFound

pytestmark = pytest.mark.unit

LITERAL_FCK_MPA: tuple[tuple[ConcreteClass, float], ...] = (
    ("C8/10", 8.0), ("C12/15", 12.0), ("C16/20", 16.0), ("C20/25", 20.0),
    ("C25/30", 25.0), ("C28/35", 28.0), ("C30/37", 30.0), ("C32/40", 32.0),
    ("C35/45", 35.0), ("C40/50", 40.0), ("C45/55", 45.0), ("C50/60", 50.0),
)


@pytest.mark.parametrize(("classe", "expected_fck"), LITERAL_FCK_MPA)
def test_fck_standard_is_ntc_literal(classe, expected_fck):
    assert fck(classe, legacy_compat=False) == pytest.approx(expected_fck)


def test_c35_45_divergence_between_legacy_and_standard():
    """docs/divergences/materials.md — the sheets' fill-down (0.83*Rck=37.35) disagrees with the
    NTC2018 Tab. 4.1.I literal (35) for this one class."""
    legacy = concrete_properties("C35/45", legacy_compat=True)
    standard = concrete_properties("C35/45", legacy_compat=False)
    assert legacy.fck_MPa == pytest.approx(37.35)
    assert standard.fck_MPa == pytest.approx(35.0)
    assert legacy.fck_MPa != pytest.approx(standard.fck_MPa)


@pytest.mark.parametrize(
    ("classe", "fck_mpa"),
    [("C20/25", 20.0), ("C50/60", 50.0)],
)
def test_formula_chain(classe, fck_mpa):
    props = concrete_properties(classe, legacy_compat=False)
    assert props.fcm_MPa == pytest.approx(fcm(fck_mpa))
    assert props.ecm_MPa == pytest.approx(ecm(fcm(fck_mpa)))
    assert props.fctm_MPa == pytest.approx(fctm(fck_mpa))
    assert props.fctk_MPa == pytest.approx(fctk(fctm(fck_mpa)))
    assert props.fcd_MPa == pytest.approx(fcd(fck_mpa))
    assert props.fctd_MPa == pytest.approx(fctd(fctk(fctm(fck_mpa))))


def test_fcd_uses_alpha_cc_and_gamma_c():
    assert fcd(30.0, gamma_c=1.5, alpha_cc=0.85) == pytest.approx(0.85 * 30.0 / 1.5)
    assert fcd(30.0, gamma_c=1.0, alpha_cc=1.0) == pytest.approx(30.0)


def test_unknown_class_raises_key_not_found():
    with pytest.raises(KeyNotFound):
        concrete_properties("C99/99")


