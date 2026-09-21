"""Crack-control sigma_s-limit table tests: exact rows vs `ca-travi` Tabelle!N67:R93, plus
interpolation (code-standard) vs exact-match (legacy_compat) lookup modes.
"""
import pytest

from strutture.shared.rebar_catalog import sigma_limit_by_diameter, sigma_limit_by_spacing
from strutture.shared.tables import KeyNotFound

pytestmark = pytest.mark.unit


# Tabelle!N67:R93 (rows verbatim from build/data/ca-travi/tabelle.csv).
@pytest.mark.parametrize(
    ("w_class", "diameter_mm", "expected_sigma"),
    [
        ("w3", 10.0, 360.0),
        ("w3", 20.0, 240.0),
        ("w3", 32.0, 200.0),
        ("w3", 40.0, 160.0),
        ("w2", 8.0, 360.0),
        ("w2", 25.0, 200.0),
        ("w2", 32.0, 160.0),
        ("w1", 6.0, 320.0),
        ("w1", 16.0, 200.0),
        ("w1", 25.0, 160.0),
    ],
)
def test_sheet_rows_match_exact_lookup(w_class, diameter_mm, expected_sigma):
    assert sigma_limit_by_diameter(diameter_mm, w_class, legacy_compat=True) == pytest.approx(expected_sigma)


def test_legacy_compat_raises_for_diameter_missing_from_table():
    # 15mm is not a standard row in Tab. C4.1.II -> the sheet's VLOOKUP(..., FALSE) raises #N/A.
    with pytest.raises(KeyNotFound):
        sigma_limit_by_diameter(15.0, "w3", legacy_compat=True)


def test_code_standard_interpolates_between_bracketing_rows():
    # w3: 14mm->300, 16mm->280 -> midpoint 15mm should interpolate to 290.
    assert sigma_limit_by_diameter(15.0, "w3", legacy_compat=False) == pytest.approx(290.0)


def test_code_standard_matches_exact_at_table_rows():
    assert sigma_limit_by_diameter(20.0, "w3", legacy_compat=False) == pytest.approx(240.0)


def test_rejects_non_positive_diameter():
    with pytest.raises(ValueError):
        sigma_limit_by_diameter(0.0, "w3")


# NTC2018 Tab. C4.1.III / EN1992-1-1 Tab. 7.3N, wk=0.3mm column (w2): spacing [mm] -> sigma_s [MPa].
@pytest.mark.parametrize(
    ("w_class", "spacing_mm", "expected_sigma"),
    [
        ("w2", 50.0, 360.0),
        ("w2", 100.0, 320.0),
        ("w2", 150.0, 280.0),
        ("w2", 200.0, 240.0),
        ("w2", 250.0, 200.0),
        ("w2", 300.0, 160.0),
    ],
)
def test_spacing_table_exact_rows(w_class, spacing_mm, expected_sigma):
    assert sigma_limit_by_spacing(spacing_mm, w_class, legacy_compat=True) == pytest.approx(expected_sigma)


def test_spacing_table_interpolates():
    # w2: 200mm->240, 250mm->200 -> midpoint 225mm should interpolate to 220.
    assert sigma_limit_by_spacing(225.0, "w2", legacy_compat=False) == pytest.approx(220.0)


def test_spacing_legacy_compat_raises_for_missing_key():
    with pytest.raises(KeyNotFound):
        sigma_limit_by_spacing(180.0, "w3", legacy_compat=True)


def test_spacing_rejects_non_positive():
    with pytest.raises(ValueError):
        sigma_limit_by_spacing(0.0, "w3")


def test_spacing_table_differs_per_w_class():
    # w1 (0.2mm) is stricter than w3 (0.4mm) at the same spacing.
    w3_sigma = sigma_limit_by_spacing(200.0, "w3", legacy_compat=True)
    w1_sigma = sigma_limit_by_spacing(200.0, "w1", legacy_compat=True)
    assert w1_sigma < w3_sigma
