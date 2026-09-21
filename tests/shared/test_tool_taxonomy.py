"""Sanity checks for the canonical sidebar taxonomy and the hint contract (docs/ui/DESIGN_SPEC.md
§4). Every discovered `Tool` must sit under one of the canonical `Tool.group` strings, carry a
clean sentence-case title, and expose an `example` that describes default-mode inputs (no
`legacy_compat`) with a sane number of `highlight` output fields.
"""
from typing import Any

from strutture.shared.tool import discover

CANONICAL_GROUPS = {
    "Carichi / Neve",
    "Carichi / Sisma",
    "Carichi / Vento",
    "Calcestruzzo armato / Travi",
    "Calcestruzzo armato / Pilastri",
    "Calcestruzzo armato / Mensole",
    "Calcestruzzo armato / Fessurazione",
    "Calcestruzzo armato / Punzonamento",
    "Acciaio / Colonne",
    "Acciaio / Sezioni",
    "Acciaio / Fuoco",
    "Geotecnica / Cedimenti",
    "Geotecnica / Muri di sostegno",
    "Fondazioni / Plinti",
    "Fondazioni / Travi di collegamento",
    "Fondazioni / Pavimenti industriali",
}


def _highlight_count(schema: dict[str, Any], defs: dict[str, Any], seen: set[str] | None = None) -> int:
    """Count distinct `highlight: true` output fields, following `$ref`/tuple `items`/
    `prefixItems`, de-duplicated by referenced `$defs` name so a submodel reused by more than one
    field (e.g. a governing row reused verbatim from a table) is only counted once."""
    if seen is None:
        seen = set()
    count = 0
    for sub in schema.get("properties", {}).values():
        if sub.get("highlight") is True:
            count += 1
        options = [sub, *sub.get("anyOf", []), *sub.get("oneOf", [])]
        refs = [o["$ref"] for o in options if "$ref" in o]
        items = sub.get("items") or {}
        if "$ref" in items:
            refs.append(items["$ref"])
        for prefix_item in sub.get("prefixItems", []) or []:
            if "$ref" in prefix_item:
                refs.append(prefix_item["$ref"])
        for ref in refs:
            def_name = ref.split("/")[-1]
            if def_name in seen:
                continue
            seen.add(def_name)
            count += _highlight_count({**defs[def_name], "$defs": defs}, defs, seen)
    return count


def test_every_tool_group_is_canonical():
    tools = discover()
    offenders = {name: tool.group for name, tool in tools.items() if tool.group not in CANONICAL_GROUPS}
    assert not offenders, f"non-canonical Tool.group values: {offenders}"


def test_every_tool_title_has_no_arrow():
    tools = discover()
    offenders = {name: tool.title for name, tool in tools.items() if "→" in tool.title}
    assert not offenders, f"tool titles still contain an arrow: {offenders}"


def test_every_tool_has_an_example_without_legacy_compat():
    tools = discover()
    for name, tool in sorted(tools.items()):
        assert tool.example is not None, f"{name}: missing example"
        assert "legacy_compat" not in tool.example, f"{name}: example still carries legacy_compat"


def test_at_most_three_highlighted_outputs():
    """DESIGN_SPEC §4: ≤3 governing results per tool. Zero is legitimate for table-only tools and for the
    seismic step tools, whose output models are shared with `sisma-completo` (already at the limit)."""
    tools = discover()
    for name, tool in sorted(tools.items()):
        out_schema = tool.output_model.model_json_schema()
        defs = out_schema.get("$defs", {})
        count = _highlight_count(out_schema, defs)
        assert count <= 3, f"{name}: {count} highlighted output fields (expected at most 3)"
