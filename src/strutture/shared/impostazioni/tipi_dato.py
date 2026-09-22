"""Classify a tool's numeric input field into a `TipoDato` (WORKBENCH_SPEC.md §26.4), from the
same schema info `GET /api/tools/{name}/schema` already serves (unit, symbol, name, JSON type)."""
from typing import Any

from .modelli import TipoDato

_UNITA_LUNGHEZZA = {"m": "lunghezza_m", "cm": "lunghezza_cm", "mm": "lunghezza_mm"}
_SIMBOLI_DIAMETRO = ("⌀", "φ", "Φ")
_SIMBOLI_SPESSORE_PREFISSO = "t_"
_SIMBOLI_SPESSORE_ESATTI = ("h_f",)


def tipo_dato(nome: str, schema_campo: dict[str, Any]) -> TipoDato | None:
    """First matching rule wins (§26.4, rules 0-7); `None` = no type step for this field."""
    hint = schema_campo.get("tipo_dato")
    if hint:
        return hint
    if _e_intero(schema_campo):
        return "intero"
    unita = schema_campo.get("unit")
    if unita not in _UNITA_LUNGHEZZA:
        return None
    simbolo = schema_campo.get("symbol", "") or ""
    nome_minuscolo = nome.lower()
    if "copriferro" in nome_minuscolo or nome_minuscolo in ("c_mm", "cf_mm"):
        return "copriferro"
    if simbolo.startswith(_SIMBOLI_DIAMETRO) or (not simbolo and "diametro" in nome_minuscolo):
        return "diametro_armatura"
    if "passo" in nome_minuscolo or "interferro" in nome_minuscolo:
        return "passo_armatura"
    if simbolo.startswith(_SIMBOLI_SPESSORE_PREFISSO) or simbolo in _SIMBOLI_SPESSORE_ESATTI or "spessore" in nome_minuscolo:
        return "spessore"
    return _UNITA_LUNGHEZZA[unita]


def _e_intero(schema_campo: dict[str, Any]) -> bool:
    tipo_json = schema_campo.get("type")
    if tipo_json == "integer":
        return True
    for ramo in schema_campo.get("anyOf", ()):
        if isinstance(ramo, dict) and ramo.get("type") == "integer":
            return True
    return False
