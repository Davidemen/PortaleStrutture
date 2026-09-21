"""Minimum-cover table tests vs `ca-travi`/`ca-pilastri` Tabelle!M14:R20 / M23:R29."""
import pytest

from strutture.shared.durability_cover import min_cover_mm
from strutture.shared.tables import KeyNotFound

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("structural_class", "exposure_class", "expected_mm"),
    [
        (1, "X0", 10.0),
        (1, "XC4", 15.0),
        (3, "XC1", 10.0),   # ca-travi golden case: S=3, esposizione XC1 -> cmin,dur=10 (Tabelle!E30)
        (4, "XC1", 15.0),   # ca-pilastri golden case: S=4, esposizione XC1 -> cmin,dur=15 (Tabelle!E30)
        (6, "XC4", 40.0),
    ],
)
def test_min_cover_ordinaria_matches_sheet(structural_class, exposure_class, expected_mm):
    assert min_cover_mm(structural_class, exposure_class, "ordinaria") == pytest.approx(expected_mm)


@pytest.mark.parametrize(
    ("structural_class", "exposure_class", "expected_mm"),
    [
        (1, "X0", 10.0),
        (1, "XC4", 25.0),
        (3, "XC1", 20.0),   # ca-travi golden case: S=3, esposizione XC1 -> cmin,dur=20 (Tabelle!E31)
        (4, "XC1", 25.0),   # ca-pilastri golden case: S=4, esposizione XC1 -> cmin,dur=25 (Tabelle!E31)
        (6, "XC4", 50.0),
    ],
)
def test_min_cover_precompressa_matches_sheet(structural_class, exposure_class, expected_mm):
    assert min_cover_mm(structural_class, exposure_class, "precompressa") == pytest.approx(expected_mm)


def test_min_cover_defaults_to_ordinaria():
    assert min_cover_mm(3, "XC2") == min_cover_mm(3, "XC2", "ordinaria")


def test_min_cover_rejects_unknown_structural_class():
    with pytest.raises(KeyNotFound):
        min_cover_mm(7, "XC2")  # type: ignore[arg-type]
