"""Enumerate the numeric inputs of a tool: shared by validation, resolution and the `/tipi` route.

Inputs are flat (`docs/BUILD_CONTRACT.md`): tables, enums, booleans and `legacy_compat` are not
"numeric" fields an office step can apply to."""
from collections.abc import Iterator
from typing import Any

from strutture.shared.tool import Tool

_CAMPO_ESCLUSO = "legacy_compat"


def campi_numerici(tool: Tool) -> Iterator[tuple[str, dict[str, Any]]]:
    """(nome campo, schema del campo) di ogni ingresso numerico del tool, ordine dei model_fields."""
    schema = tool.input_model.model_json_schema()
    proprieta = schema.get("properties", {})
    for nome in tool.input_model.model_fields:
        if nome == _CAMPO_ESCLUSO:
            continue
        campo = proprieta.get(nome, {})
        if _e_numerico(campo):
            yield nome, campo


def _e_numerico(campo: dict[str, Any]) -> bool:
    if "enum" in campo:
        return False
    tipi = _tipi_json(campo)
    return bool(tipi & {"integer", "number"})


def _tipi_json(campo: dict[str, Any]) -> set[str]:
    if "type" in campo:
        return {campo["type"]}
    return {ramo.get("type") for ramo in campo.get("anyOf", ()) if isinstance(ramo, dict) and "type" in ramo}
