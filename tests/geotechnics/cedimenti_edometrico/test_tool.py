"""Tool-level tests: registration, the `example` golden case, and the UI hint contract
(BUILD_CONTRACT "Batch 2": group/symbol/unit or unit_options/advanced/highlight/chart)."""
import pytest

from strutture.geotechnics.cedimenti_edometrico.models import EdometricoInput
from strutture.geotechnics.cedimenti_edometrico.tool import TOOLS


def _tool():
    return TOOLS[0]


@pytest.mark.unit
def test_single_tool_registered() -> None:
    assert len(TOOLS) == 1
    assert TOOLS[0].name == "geo-cedimento-edometrico"


@pytest.mark.unit
def test_example_validates_and_runs() -> None:
    tool = _tool()
    inputs = tool.input_model.model_validate(tool.example)
    report = tool.run(inputs)
    assert report.ok


@pytest.mark.unit
def test_example_matches_the_golden_case() -> None:
    report = _tool().run(EdometricoInput.model_validate(_tool().example))
    assert report.data.cedimento.w_ed_cm == pytest.approx(2.9958, rel=1e-4)


@pytest.mark.unit
def test_every_input_field_has_a_group() -> None:
    schema = EdometricoInput.model_json_schema()
    for name, prop in schema["properties"].items():
        assert "group" in prop, f"campo {name} senza 'group'"


@pytest.mark.unit
def test_model_carries_the_unit_selector_hint() -> None:
    schema = EdometricoInput.model_json_schema()
    assert schema.get("unit_selector") == "sistema_unita"


@pytest.mark.unit
def test_dimensional_fields_carry_unit_options_or_unit() -> None:
    schema = EdometricoInput.model_json_schema()
    for name in ("b", "l", "gamma", "q", "z_crit_input", "dz", "z_max", "falda"):
        assert "unit_options" in schema["properties"][name], f"campo {name} senza 'unit_options'"
    assert schema["properties"]["d"].get("unit") == "m"


@pytest.mark.unit
def test_advanced_fields_are_marked() -> None:
    schema = EdometricoInput.model_json_schema()
    for name in ("legacy_compat", "z_crit_input", "dz", "z_max", "falda"):
        assert schema["properties"][name].get("advanced") is True, f"campo {name} non 'advanced'"


@pytest.mark.unit
def test_output_has_at_most_three_highlights() -> None:
    schema = _tool().output_model.model_json_schema()
    defs = schema.get("$defs", {})
    highlights = [
        prop.get("highlight")
        for definition in (*defs.values(), schema)
        for prop in definition.get("properties", {}).values()
    ]
    assert 1 <= sum(bool(h) for h in highlights) <= 3


@pytest.mark.unit
def test_righe_field_carries_a_chart_hint() -> None:
    schema = _tool().output_model.model_json_schema()
    righe_prop = schema["properties"]["righe"]
    chart = righe_prop.get("chart")
    assert chart is not None
    assert chart["x"] == "z_m"
    row_schema = schema["$defs"][righe_prop["items"]["$ref"].rsplit("/", 1)[-1]]
    for column in [chart["x"], *chart["y"]]:
        assert column in row_schema["properties"], f"colonna {column} non presente in RigaResult"
