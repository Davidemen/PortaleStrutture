"""UI-hint contract (docs/ui/DESIGN_SPEC.md §4): every input has a `group`, at most 3
`highlight` outputs per tool, and each `Tool.example` validates and runs without error."""
import pytest

from strutture.members.ca_fessurazione.tool import TOOLS

pytestmark = pytest.mark.unit

TOOL_NAMES = ["ca-sle-limitazione-tensioni", "ca-apertura-fessure", "ca-apertura-fessure-semplificata"]


@pytest.mark.parametrize("name", TOOL_NAMES)
def test_example_validates_and_runs(name):
    tool = next(t for t in TOOLS if t.name == name)
    inputs = tool.input_model.model_validate(tool.example)
    report = tool.run(inputs)
    assert report.ok


@pytest.mark.parametrize("name", TOOL_NAMES)
def test_every_input_has_a_group(name):
    tool = next(t for t in TOOLS if t.name == name)
    schema = tool.input_model.model_json_schema()
    for nome, prop in schema["properties"].items():
        assert prop.get("group"), f"{name}.{nome} manca del gruppo UI"


@pytest.mark.parametrize("name", TOOL_NAMES)
def test_at_most_three_highlighted_outputs(name):
    tool = next(t for t in TOOLS if t.name == name)
    schema = tool.output_model.model_json_schema()
    defs = schema.get("$defs", {})
    top_level = [nome for nome, prop in schema.get("properties", {}).items() if prop.get("highlight")]
    nested = [
        nome
        for def_ in defs.values()
        for nome, prop in def_.get("properties", {}).items()
        if prop.get("highlight")
    ]
    highlighted = top_level + nested
    assert 0 < len(highlighted) <= 3
