"""UI hints are part of the job (`docs/BUILD_CONTRACT.md` "Batch 2"): group / symbol / unit or
unit_options / advanced / condition / highlight (<=3) / chart / `Tool.example`."""
import pytest

from strutture.geotechnics.cedimenti_elastico.tool_newmark import TOOLS as NEWMARK_TOOLS
from strutture.geotechnics.cedimenti_elastico.tool_timoshenko_goodier import TOOLS as TG_TOOLS
from strutture.shared.tool import execute

ALL_TOOLS = (*NEWMARK_TOOLS, *TG_TOOLS)


def _highlighted_output_fields(model, prefix=""):
    found = []
    for name, field in model.model_fields.items():
        extra = field.json_schema_extra or {}
        if isinstance(extra, dict) and extra.get("highlight"):
            found.append(f"{prefix}{name}")
        annotation = field.annotation
        nested = getattr(annotation, "__args__", (annotation,))
        for candidate in nested:
            if hasattr(candidate, "model_fields") and candidate is not model:
                found.extend(_highlighted_output_fields(candidate, prefix=f"{prefix}{name}."))
    return found


@pytest.mark.unit
@pytest.mark.parametrize("tool", ALL_TOOLS, ids=[t.name for t in ALL_TOOLS])
def test_every_dimensional_scalar_input_has_group_and_symbol_and_unit(tool):
    for name, field in tool.input_model.model_fields.items():
        if name in ("strati", "legacy_compat"):
            continue
        extra = field.json_schema_extra or {}
        assert isinstance(extra, dict), name
        assert "group" in extra, f"{name}: missing group"
        if field.annotation in (float, float | None):
            assert "symbol" in extra, f"{name}: missing symbol"
            assert "unit" in extra or "unit_options" in extra, f"{name}: missing unit/unit_options"


@pytest.mark.unit
@pytest.mark.parametrize("tool", ALL_TOOLS, ids=[t.name for t in ALL_TOOLS])
def test_legacy_compat_and_advanced_fields_are_marked_advanced(tool):
    for name in ("legacy_compat",):
        extra = tool.input_model.model_fields[name].json_schema_extra or {}
        assert extra.get("advanced") is True, name


@pytest.mark.unit
@pytest.mark.parametrize("tool", ALL_TOOLS, ids=[t.name for t in ALL_TOOLS])
def test_at_most_three_highlighted_outputs(tool):
    highlighted = _highlighted_output_fields(tool.output_model)
    assert 1 <= len(highlighted) <= 3, highlighted


def _highlighted_field_extras(model, prefix=""):
    found = []
    for name, field in model.model_fields.items():
        extra = field.json_schema_extra or {}
        if isinstance(extra, dict) and extra.get("highlight"):
            found.append((f"{prefix}{name}", extra, field.description or ""))
        annotation = field.annotation
        nested = getattr(annotation, "__args__", (annotation,))
        for candidate in nested:
            if hasattr(candidate, "model_fields") and candidate is not model:
                found.extend(_highlighted_field_extras(candidate, prefix=f"{prefix}{name}."))
    return found


@pytest.mark.unit
@pytest.mark.parametrize("tool", ALL_TOOLS, ids=[t.name for t in ALL_TOOLS])
def test_highlighted_fields_have_a_symbol_and_no_formula_in_description(tool):
    """Design-review finding: a highlighted output with no `symbol` renders as a long italic
    description in the Sintesi summary; descriptions must read as prose, not as a formula."""
    for name, extra, description in _highlighted_field_extras(tool.output_model):
        assert extra.get("symbol"), f"{tool.name}.{name}: highlighted field has no symbol"
        assert "=" not in description, f"{tool.name}.{name}: description looks like a formula: {description!r}"


@pytest.mark.unit
def test_newmark_condition_hints_gate_mode_specific_fields():
    fields = NEWMARK_TOOLS[0].input_model.model_fields
    assert fields["b"].json_schema_extra["condition"] == {"field": "modalita", "equals": ["CENTRO"]}
    assert fields["side_p"].json_schema_extra["condition"] == {"field": "modalita", "equals": ["PUNTO"]}


@pytest.mark.unit
def test_model_level_unit_selector_hint_is_present():
    for tool in ALL_TOOLS:
        extra = tool.input_model.model_config.get("json_schema_extra") or {}
        assert extra.get("unit_selector") == "sistema_unita"


@pytest.mark.unit
def test_righe_output_carries_a_chart_hint():
    extra = NEWMARK_TOOLS[0].output_model.model_fields["righe"].json_schema_extra or {}
    assert "chart" in extra
    assert extra["chart"]["x"] == "z_m"


@pytest.mark.unit
@pytest.mark.parametrize("tool", ALL_TOOLS, ids=[t.name for t in ALL_TOOLS])
def test_example_validates_and_runs(tool):
    assert tool.example is not None
    report = execute(tool, tool.example)
    assert report.ok, report.errors
