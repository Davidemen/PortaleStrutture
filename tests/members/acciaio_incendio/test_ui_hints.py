"""Sanity checks for the UI hints applied to the `acciaio_incendio` package models (docs/ui/DESIGN_SPEC.md §4)."""
from typing import Any

from strutture.members.acciaio_incendio.tool import TOOLS


def _resolve(schema: dict[str, Any], defs: dict[str, Any]) -> dict[str, Any]:
    """Flatten a pydantic JSON schema into {field_name: field_schema}, dotted for nested models."""
    out: dict[str, Any] = {}
    for name, sub in schema.get("properties", {}).items():
        options = [sub, *sub.get("anyOf", []), *sub.get("oneOf", [])]
        ref = next((defs[o["$ref"].split("/")[-1]] for o in options if "$ref" in o), None)
        out[name] = sub
        if ref is not None:
            for nested_name, nested_schema in _resolve({**ref, "$defs": defs}, defs).items():
                out[f"{name}.{nested_name}"] = nested_schema
        items = sub.get("items") or {}
        item_ref = defs.get(items.get("$ref", "").split("/")[-1]) if "$ref" in items else None
        if item_ref is not None:
            for col_name, col_schema in item_ref.get("properties", {}).items():
                out[f"{name}.{col_name}"] = col_schema
    return out


def _highlight_count(schema: dict[str, Any], defs: dict[str, Any]) -> int:
    return sum(1 for f in _resolve(schema, defs).values() if f.get("highlight") is True)


def test_all_tool_examples_run_ok():
    for tool in TOOLS:
        assert tool.example is not None, f"{tool.name}: missing example"
        inputs = tool.input_model.model_validate(tool.example)
        report = tool.run(inputs)
        assert report.ok, f"{tool.name}: example failed -> {report.errors}"


def test_highlight_count_at_most_three():
    for tool in TOOLS:
        out_schema = tool.output_model.model_json_schema()
        defs = out_schema.get("$defs", {})
        count = _highlight_count(out_schema, defs)
        assert count <= 3, f"{tool.name}: {count} highlighted output fields (max 3)"


def test_group_and_condition_and_chart_refer_to_real_fields():
    for tool in TOOLS:
        in_schema = tool.input_model.model_json_schema()
        in_defs = in_schema.get("$defs", {})
        in_fields = _resolve(in_schema, in_defs)

        out_schema = tool.output_model.model_json_schema()
        out_defs = out_schema.get("$defs", {})
        out_fields = _resolve(out_schema, out_defs)

        for name, field_schema in in_fields.items():
            condition = field_schema.get("condition")
            if condition is not None:
                assert condition["field"] in in_fields, f"{tool.name}.{name}: condition.field {condition['field']!r} unknown"

        for name, field_schema in out_fields.items():
            chart = field_schema.get("chart")
            if chart is None:
                continue
            for axis_field in (chart["x"], *chart["y"]):
                assert f"{name}.{axis_field}" in out_fields, f"{tool.name}.{name}: chart field {axis_field!r} unknown"
