"""UI-hint contract (docs/ui/DESIGN_SPEC.md §4): every input has a `group`, at most 3
`highlight` outputs, and `Tool.example` validates and runs without error."""
import pytest

from strutture.members.ca_taglio_non_armato.compose import run
from strutture.members.ca_taglio_non_armato.models import TaglioNonArmatoInput, TaglioNonArmatoOutput
from strutture.members.ca_taglio_non_armato.tool import TOOLS

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "ca-taglio-non-armato")

GOLDEN_KWARGS = {"rck_MPa": 35, "h_mm": 500, "c_mm": 50, "bw_mm": 1000, "asl_mm2": 1005, "ned_kN": 0}


def test_golden_case_validates_and_runs():
    report = run(TaglioNonArmatoInput(legacy_compat=True, **GOLDEN_KWARGS))
    assert report.ok


def test_example_validates_and_runs_in_default_mode():
    """Tool.example must run ok in the DEFAULT mode (no legacy_compat in it, per build contract)."""
    assert "legacy_compat" not in TOOL.example
    inputs = TOOL.input_model.model_validate(TOOL.example)
    report = TOOL.run(inputs)
    assert report.ok


def test_every_input_has_a_group():
    schema = TaglioNonArmatoInput.model_json_schema()
    for nome, prop in schema["properties"].items():
        assert prop.get("group"), f"{nome} manca del gruppo UI"


def test_at_most_three_highlighted_outputs():
    schema = TaglioNonArmatoOutput.model_json_schema()
    defs = schema["$defs"]
    highlighted = [
        nome
        for def_ in defs.values()
        for nome, prop in def_.get("properties", {}).items()
        if prop.get("highlight")
    ]
    assert 0 < len(highlighted) <= 3


def test_check_has_value_limit_unit():
    report = run(TaglioNonArmatoInput(legacy_compat=True, **GOLDEN_KWARGS))
    assert report.checks
    check = report.checks[0]
    assert check.value is not None
    assert check.limit is not None
    assert check.unit
