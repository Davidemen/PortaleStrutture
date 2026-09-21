"""`TOOLS` registration + UI-hint contract (docs/BUILD_CONTRACT.md "Batch 2", docs/ui/DESIGN_SPEC.md §4)."""
import pytest

from strutture.members.ca_punzonamento.models import PunzonamentoInput, PunzonamentoOutput
from strutture.members.ca_punzonamento.tool import TOOLS

pytestmark = pytest.mark.unit


def test_tool_registered():
    assert len(TOOLS) == 1
    tool = TOOLS[0]
    assert tool.name == "ca-punzonamento"
    assert tool.input_model is PunzonamentoInput
    assert tool.output_model is PunzonamentoOutput


def test_example_validates_and_runs():
    tool = TOOLS[0]
    assert tool.example is not None
    inputs = tool.input_model.model_validate(tool.example)
    report = tool.run(inputs)
    assert report.ok


def test_every_input_field_has_group_and_description():
    schema = PunzonamentoInput.model_json_schema()
    for name, prop in schema["properties"].items():
        if name == "legacy_compat":
            continue
        assert prop.get("description"), f"{name}: missing Italian description"
        assert prop.get("group"), f"{name}: missing UI group hint"


def test_dimensional_input_fields_carry_unit_and_symbol():
    schema = PunzonamentoInput.model_json_schema()
    dimensional = {
        "ved_kN", "pterreno_MPa", "lato_a_mm", "lato_b_mm", "h_mm", "diametro_mm", "fck_MPa",
        "copriferro_mm", "px_mm", "py_mm", "phix_mm", "phiy_mm", "a1eff_mm", "bu_mm", "st_mm", "phi_staffa_mm",
    }
    for name in dimensional:
        prop = schema["properties"][name]
        assert prop.get("unit"), f"{name}: missing unit"
        assert prop.get("symbol"), f"{name}: missing symbol"


def test_position_field_is_a_dropdown_enum_with_symbol():
    prop = PunzonamentoInput.model_json_schema()["properties"]["posizione"]
    assert prop["enum"] == ["centrato", "interno", "bordo", "angolo"]
    assert prop["symbol"] == "β"


def test_diametro_field_is_conditional_on_lato_a():
    prop = PunzonamentoInput.model_json_schema()["properties"]["diametro_mm"]
    assert prop["condition"] == {"field": "lato_a_mm", "equals": [0]}


def test_advanced_fields_are_flagged():
    schema = PunzonamentoInput.model_json_schema()
    for name in ("umanuale_mm", "a_amanuale_mm2", "legacy_compat", "coeff_vrd_max"):
        assert schema["properties"][name].get("advanced") is True


def test_coeff_vrd_max_is_a_named_dropdown_defaulting_to_04():
    schema = PunzonamentoInput.model_json_schema()
    prop = schema["properties"]["coeff_vrd_max"]
    assert prop["enum"] == [0.4, 0.5]
    assert prop["default"] == 0.4


def test_at_most_three_highlighted_outputs():
    schema = PunzonamentoOutput.model_json_schema()
    highlighted = [
        (model_name, field_name)
        for model_name, model_schema in schema["$defs"].items()
        for field_name, prop in model_schema.get("properties", {}).items()
        if prop.get("highlight") is True
    ]
    assert 1 <= len(highlighted) <= 3
    assert ("PerimetroCriticoOutput", "rapporto") in highlighted
    assert ("ArmaturaOutput", "ved_su_vrd") in highlighted


def test_check_names_are_readable_italian_phrases_not_python_keys():
    """Design review (P0): `Check(name=...)` must be a readable Italian phrase, never a raw
    snake_case Python key, so no check name may contain an underscore."""
    from strutture.shared.tool import execute

    tool = TOOLS[0]
    report = execute(tool, {**tool.example, "legacy_compat": True})  # forces the armatura checks too
    assert report.ok, report.errors
    assert report.checks
    for check in report.checks:
        assert "_" not in check.name, check.name


def test_righe_field_has_chart_hint():
    schema = PunzonamentoOutput.model_json_schema()
    righe_prop = schema["$defs"]["PerimetroCriticoOutput"]["properties"]["righe"]
    chart = righe_prop["chart"]
    assert chart["x"] == "a_su_d"
    assert "v_ed_i_MPa" in chart["y"] and "v_rd_i_MPa" in chart["y"]
    assert chart["guides"][0]["field"] == "a_governante_su_d"
