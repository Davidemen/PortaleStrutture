"""Tool-level tests: registration, the `example` golden case, and output-hint contract (DESIGN_SPEC
§4: `highlight` <= 3, `chart`/`rows_page` on many-rows results)."""
import pytest

from strutture.foundations.pavimento_industriale.tool import TOOLS


def _tool():
    return TOOLS[0]


@pytest.mark.unit
def test_single_tool_registered() -> None:
    """BUILD_CONTRACT 'Member tools': ONE composed tool per sheet-level workflow."""
    assert len(TOOLS) == 1
    assert TOOLS[0].name == "fond-pavimento-industriale"


@pytest.mark.unit
def test_example_validates_and_runs() -> None:
    tool = _tool()
    inputs = tool.input_model.model_validate(tool.example)
    report = tool.run(inputs)
    assert report.ok
    assert all(check.passed for check in report.checks)


@pytest.mark.unit
def test_example_has_multiple_carichi_rows_exercising_all_positions() -> None:
    tool = _tool()
    posizioni = {row["posizione"] for row in tool.example["carichi"]}
    assert posizioni == {"centro", "bordo", "spigolo"}


@pytest.mark.unit
def test_at_most_three_highlighted_output_fields() -> None:
    tool = _tool()
    schema = tool.output_model.model_json_schema()
    highlighted = [
        (name, prop) for defn in schema.get("$defs", {}).values() for name, prop in defn.get("properties", {}).items()
        if prop.get("highlight") is True
    ]
    assert 1 <= len(highlighted) <= 3


@pytest.mark.unit
def test_righe_output_carries_rows_page_hint() -> None:
    tool = _tool()
    schema = tool.output_model.model_json_schema()
    concentrati_defn = schema["$defs"]["ConcentratiResult"]
    assert concentrati_defn["properties"]["righe"]["rows_page"] == 200
