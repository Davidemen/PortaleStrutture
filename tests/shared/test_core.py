"""Unit tests for the shared core: envelope, tool execution, lookups, numeric helpers."""
import pytest
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.numeric import clamp, lerp
from strutture.shared.report import CalcError, Check, success
from strutture.shared.tables import KeyNotFound, band_lookup, exact_lookup, interp_lookup
from strutture.shared.tool import Tool, discover, execute

pytestmark = pytest.mark.unit


class DoubleIn(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float = Field(gt=0)


class DoubleOut(BaseModel):
    model_config = ConfigDict(frozen=True)
    y: float


def run_double(inputs: DoubleIn):
    if inputs.x > 100:
        raise CalcError("x fuori dal campo di validità (max 100)")
    return success(DoubleOut(y=inputs.x * 2), inputs, checks=(Check(name="positivo", passed=True),))


DOUBLE = Tool("double", "Raddoppia", "Test", "-", DoubleIn, DoubleOut, run_double)


def test_execute_returns_data_and_echo():
    report = execute(DOUBLE, {"x": 2})
    assert report.ok and report.data.y == 4 and report.inputs_echo == {"x": 2.0}


def test_execute_maps_validation_and_domain_errors():
    invalid = execute(DOUBLE, {"x": -1})
    assert not invalid.ok and invalid.errors[0].startswith("x:")
    rejected = execute(DOUBLE, {"x": 101})
    assert not rejected.ok and "validità" in rejected.errors[0]


def test_lookups_follow_excel_semantics():
    grades = (("B450C", 450), ("B500C", 500))
    assert exact_lookup(grades, "b450c") == 450
    with pytest.raises(KeyNotFound):
        exact_lookup(grades, "B450C ", ignore_case=False)
    bands = ((0, "a"), (10, "b"), (20, "c"))
    assert band_lookup(bands, 10) == "b" and band_lookup(bands, 19.9) == "b"
    with pytest.raises(KeyNotFound):
        band_lookup(bands, -1)
    assert interp_lookup(((0, 0.0), (10, 1.0)), 2.5) == pytest.approx(0.25)
    with pytest.raises(KeyNotFound):
        interp_lookup(((0, 0.0), (10, 1.0)), 11)


def test_numeric_helpers():
    assert clamp(5, 0, 1) == 1 and clamp(-5, 0, 1) == 0
    assert lerp(5, 0, 0, 10, 100) == 50
    with pytest.raises(ValueError):
        lerp(1, 2, 0, 2, 1)


def test_discover_has_unique_tool_names():
    assert isinstance(discover(), dict)


def test_bisect_and_fixpoint_replace_goal_seek_and_circular_refs():
    import math

    from strutture.shared.numeric import bisect, fixpoint

    assert bisect(lambda x: x * x - 2, 0, 2) == pytest.approx(math.sqrt(2), abs=1e-8)
    assert bisect(lambda x: x - 1, 1, 3) == 1
    with pytest.raises(ValueError):
        bisect(lambda x: x * x + 1, -1, 1)
    assert fixpoint(math.cos, 1.0) == pytest.approx(0.7390851332, abs=1e-8)
    with pytest.raises(ValueError):
        fixpoint(lambda x: x + 1, 0.0)


def test_unit_conversions_round_trip():
    from strutture.shared import units

    assert units.kn_to_n(1.5) == 1500 and units.n_to_kn(1500) == 1.5
    assert units.m_to_mm(0.4) == 400 and units.mm_to_m(400) == 0.4
    assert units.knm_to_nmm(2) == 2_000_000 and units.nmm_to_knm(2_000_000) == 2
    assert units.mpa_to_kpa(0.2) == 200
