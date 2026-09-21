"""Fixed-behaviour tests (legacy_compat=False): EN1993-1-1 Table 3.1 thickness bands and partial
factors (docs/divergences/materials.md)."""
import pytest

from strutture.shared.materials.structural_steel import (
    fyk_fuk,
    modulo_taglio,
    partial_factors,
    steel_properties,
)
from strutture.shared.tables import KeyNotFound


@pytest.mark.parametrize(
    ("grado", "t_mm", "fyk", "fuk"),
    [
        ("S235", 40.0, 235.0, 360.0),
        ("S235", 40.1, 215.0, 360.0),
        ("S275", 80.0, 255.0, 410.0),
        ("S355", 30.0, 355.0, 510.0),
        ("S420", 50.0, 390.0, 520.0),
        ("S460", 10.0, 460.0, 540.0),
    ],
)
def test_thickness_band_selection(grado, t_mm, fyk, fuk):
    result = fyk_fuk(grado, t_mm, legacy_compat=False)
    assert result == pytest.approx((fyk, fuk))


def test_thickness_band_divergence_from_legacy():
    """docs/divergences/materials.md — the sheet always returns the t<=40mm band."""
    legacy = steel_properties("S355", 60.0, legacy_compat=True)
    standard = steel_properties("S355", 60.0, legacy_compat=False)
    assert legacy.fyk_MPa == pytest.approx(355.0)
    assert standard.fyk_MPa == pytest.approx(335.0)


def test_thickness_beyond_table_raises_key_not_found():
    with pytest.raises(KeyNotFound):
        fyk_fuk("S235", 90.0, legacy_compat=False)


def test_unknown_grade_raises_key_not_found():
    with pytest.raises(KeyNotFound):
        fyk_fuk("S999", 10.0)


def test_elastic_constants():
    assert steel_properties("S235", 10.0).e_MPa == pytest.approx(210000.0)
    assert modulo_taglio(210000.0, poisson=0.3) == pytest.approx(210000.0 / 2.6)


def test_partial_factors_default_non_bridge():
    factors = partial_factors()
    assert (factors.gamma_m0, factors.gamma_m1, factors.gamma_m2) == pytest.approx((1.05, 1.05, 1.25))


def test_partial_factors_bridge():
    factors = partial_factors(ponte=True)
    assert factors.gamma_m1 == pytest.approx(1.1)
