"""UI hints regression: highlighted output fields must carry a `symbol` and read as prose, not a
formula (design-review finding 2026-09-21: a highlight with no symbol renders as a long italic
description in the Sintesi summary)."""
from typing import Any

from strutture.geotechnics.cedimenti_edometrico.tool import TOOLS

TOOL = TOOLS[0]


def _resolve(schema: dict[str, Any], defs: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a pydantic JSON schema into {field_name: field_schema}, dotted for nested models."""
    out: dict[str, Any] = {}
    for name, sub in schema.get("properties", {}).items():
        options = [sub, *sub.get("anyOf", []), *sub.get("oneOf", [])]
        ref = next((defs[o["$ref"].split("/")[-1]] for o in options if "$ref" in o), None)
        out[f"{prefix}{name}"] = sub
        if ref is not None:
            out.update(_resolve({**ref, "$defs": defs}, defs, prefix=f"{prefix}{name}."))
        items = sub.get("items") or {}
        item_ref = defs.get(items.get("$ref", "").split("/")[-1]) if "$ref" in items else None
        if item_ref is not None:
            out.update(_resolve({**item_ref, "$defs": defs}, defs, prefix=f"{prefix}{name}."))
    return out


def test_highlighted_fields_have_a_symbol_and_no_formula_in_description() -> None:
    schema = TOOL.output_model.model_json_schema()
    defs = schema.get("$defs", {})
    for name, field_schema in _resolve(schema, defs).items():
        if field_schema.get("highlight") is not True:
            continue
        assert field_schema.get("symbol"), f"{name}: highlighted field has no symbol"
        description = field_schema.get("description", "")
        assert "=" not in description, f"{name}: description looks like a formula: {description!r}"
