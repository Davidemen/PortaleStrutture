"""Bar area/count/callout unit tests, hand-computed against pi/4*d^2."""
import math

import pytest

from strutture.shared.rebar_catalog import bar_area, bar_callout, bars_area, bars_needed

pytestmark = pytest.mark.unit


def test_bar_area_phi16():
    assert bar_area(16.0) == pytest.approx(math.pi / 4 * 16.0**2, rel=1e-9)


def test_bar_area_phi16_matches_known_value():
    # Standard rebar table: Ø16 -> 201.06 mm^2
    assert bar_area(16.0) == pytest.approx(201.06, rel=1e-3)


@pytest.mark.parametrize("diameter_mm", [0, -5])
def test_bar_area_rejects_non_positive(diameter_mm):
    with pytest.raises(ValueError):
        bar_area(diameter_mm)


def test_bars_area_multiplies_by_count():
    assert bars_area(4, 16.0) == pytest.approx(4 * bar_area(16.0), rel=1e-9)


def test_bars_area_zero_bars_is_zero():
    assert bars_area(0, 16.0) == 0.0


def test_bars_area_rejects_negative_count():
    with pytest.raises(ValueError):
        bars_area(-1, 16.0)


def test_bars_needed_rounds_up():
    # As_req slightly above 3 bars of Ø16 (603.19 mm^2) must need a 4th bar.
    as_req = 3 * bar_area(16.0) + 1.0
    assert bars_needed(as_req, 16.0) == 4


def test_bars_needed_exact_multiple():
    assert bars_needed(4 * bar_area(16.0), 16.0) == 4


def test_bars_needed_zero_area_needs_no_bars():
    assert bars_needed(0.0, 16.0) == 0


def test_bars_needed_rejects_negative_area():
    with pytest.raises(ValueError):
        bars_needed(-1.0, 16.0)


def test_bar_callout_integer_diameter():
    assert bar_callout(4, 16) == "4ø16"


def test_bar_callout_float_whole_diameter():
    assert bar_callout(4, 16.0) == "4ø16"


def test_bar_callout_rejects_negative_count():
    with pytest.raises(ValueError):
        bar_callout(-1, 16)
