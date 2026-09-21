"""UI-hint contract (docs/ui/DESIGN_SPEC.md §4): every scalar input has a `group`, at most 3
`highlight` outputs, and each `Tool.example` validates and runs without error."""
import pytest

from strutture.members.ca_pilastri.tool import TOOLS

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("name", ["ca-pilastro-rettangolare", "ca-pilastro-circolare"])
def test_example_validates_and_runs(name):
    tool = next(t for t in TOOLS if t.name == name)
    inputs = tool.input_model.model_validate(tool.example)
    report = tool.run(inputs)
    assert report.ok


@pytest.mark.parametrize("name", ["ca-pilastro-rettangolare", "ca-pilastro-circolare"])
def test_every_input_has_a_group(name):
    tool = next(t for t in TOOLS if t.name == name)
    schema = tool.input_model.model_json_schema()
    for nome, prop in schema["properties"].items():
        assert prop.get("group"), f"{nome} manca del gruppo UI"


def test_at_most_three_highlighted_outputs():
    tool = TOOLS[0]
    schema = tool.output_model.model_json_schema()
    defs = schema["$defs"]
    highlighted = [
        nome
        for def_ in defs.values()
        for nome, prop in def_.get("properties", {}).items()
        if prop.get("highlight")
    ]
    assert 0 < len(highlighted) <= 3
