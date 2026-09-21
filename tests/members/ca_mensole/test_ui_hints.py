"""UI-hint contract (docs/ui/DESIGN_SPEC.md §4): every input has a `group`, at most 3
`highlight` outputs, and `Tool.example` validates and runs without error."""
import pytest

from strutture.members.ca_mensole.tool import TOOLS

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "ca-mensola-tozza")


def test_example_validates_and_runs():
    inputs = TOOL.input_model.model_validate(TOOL.example)
    report = TOOL.run(inputs)
    assert report.ok


def test_every_input_has_a_group():
    schema = TOOL.input_model.model_json_schema()
    for nome, prop in schema["properties"].items():
        assert prop.get("group"), f"{nome} manca del gruppo UI"


def test_at_most_three_highlighted_outputs():
    schema = TOOL.output_model.model_json_schema()
    defs = schema["$defs"]
    highlighted = [
        nome
        for def_ in defs.values()
        for nome, prop in def_.get("properties", {}).items()
        if prop.get("highlight")
    ]
    assert 0 < len(highlighted) <= 3
