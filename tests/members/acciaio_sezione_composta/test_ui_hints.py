"""UI-hint contract (BUILD_CONTRACT "Member tools"/"Batch 2"): every input has a `group`, the
table field carries the `widget: table` hints, at most 3 `highlight` outputs, and `Tool.example`
validates and runs without error."""
import pytest

from strutture.members.acciaio_sezione_composta.tool import TOOLS

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "acciaio-sezione-h-rimpiattata")


def test_every_scalar_input_has_a_group():
    schema = TOOL.input_model.model_json_schema()
    for nome, prop in schema["properties"].items():
        if nome in ("piatti", "legacy_compat"):
            continue  # table field / always-advanced toggle, not grouped with the ordinary fields
        assert prop.get("group"), f"{nome} manca del gruppo UI"


def test_piatti_table_field_has_table_widget_hints():
    schema = TOOL.input_model.model_json_schema()
    piatti = schema["properties"]["piatti"]
    assert piatti["widget"] == "table"
    assert piatti["table"]["fixed_rows"] is False


def test_at_most_three_highlighted_outputs():
    schema = TOOL.output_model.model_json_schema()
    sezione = schema["$defs"]["Sezione"]
    highlighted = [nome for nome, prop in sezione["properties"].items() if prop.get("highlight")]
    assert 0 < len(highlighted) <= 3


def test_example_validates_and_runs():
    inputs = TOOL.input_model.model_validate(TOOL.example)
    report = TOOL.run(inputs)
    assert report.ok


@pytest.mark.parametrize("nome", ["h_profilo_mm", "b_profilo_mm", "tf_mm", "tw_mm"])
def test_scalar_inputs_carry_unit_and_symbol(nome):
    schema = TOOL.input_model.model_json_schema()
    prop = schema["properties"][nome]
    assert prop.get("unit")
    assert prop.get("symbol")
