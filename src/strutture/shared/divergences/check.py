"""Register consistency checks: unknown tools, missing outputs, duplicate titles, empty
`clausola`, and orphan `legacy()` ids (register vs. code, both directions).

`python -m strutture.shared.divergences.check` runs every check against the packaged register
and the real tool discovery / source tree, prints the report, and exits 1 only on errors
(warnings do not fail the build; "non ancora collegati" ids are expected until the linkage step).
"""
import ast
from dataclasses import dataclass
from pathlib import Path

from strutture.shared.tool import Tool, discover

from .loader import load_register
from .models import Divergence

REPO_SRC = Path(__file__).resolve().parents[2]  # .../src/strutture
WARN_TIPI = ("errore_foglio", "aggiornamento_normativo")


@dataclass(frozen=True)
class CheckReport:
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def exit_code(self) -> int:
        return 1 if self.errors else 0


def unknown_tool_errors(register: tuple[Divergence, ...], known_tools: frozenset[str]) -> tuple[str, ...]:
    return tuple(
        f"{d.id}: unknown tool {name!r} (not in strutture.shared.tool.discover())"
        for d in register
        for name in d.strumenti
        if name not in known_tools
    )


def unknown_output_errors(register: tuple[Divergence, ...], tools: dict[str, Tool]) -> tuple[str, ...]:
    """A path must exist in the output schema of AT LEAST ONE of the entry's tools: the same divergence
    often affects tools whose outputs are structured differently."""
    errors: list[str] = []
    for d in register:
        schemas = [tools[name].output_model.model_json_schema() for name in d.strumenti if name in tools]
        if not schemas:
            continue  # unknown tools are reported by unknown_tool_errors
        known = sorted(name for name in d.strumenti if name in tools)
        errors += [
            f"{d.id}: output path {path!r} not found in the output schema of any of {known}"
            for path in d.uscite
            if not any(_path_exists(schema, schema.get("$defs", {}), path) for schema in schemas)
        ]
    return tuple(errors)


def duplicate_title_errors(register: tuple[Divergence, ...]) -> tuple[str, ...]:
    errors: list[str] = []
    seen_by_unit: dict[str, dict[str, str]] = {}
    for d in register:
        unit = d.id.split("/", 1)[0]
        seen = seen_by_unit.get(unit, {})
        if d.titolo in seen:
            errors.append(f"{d.id}: duplicate titolo {d.titolo!r} within unit {unit!r} (also {seen[d.titolo]})")
        seen_by_unit[unit] = {**seen, d.titolo: d.id}
    return tuple(errors)


def empty_clausola_warnings(register: tuple[Divergence, ...]) -> tuple[str, ...]:
    return tuple(
        f"{d.id}: tipo={d.tipo} but clausola is empty"
        for d in register
        if d.tipo in WARN_TIPI and not d.clausola.strip()
    )


def legacy_ids_in_code(code_root: Path) -> frozenset[str]:
    """Every string literal passed as the first argument of a `legacy(...)` call under `code_root`."""
    ids: set[str] = set()
    for path in sorted(code_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_legacy_call(node.func) and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    ids.add(first.value)
    return frozenset(ids)


def _is_legacy_call(func: ast.expr) -> bool:
    if isinstance(func, ast.Name):
        return func.id == "legacy"
    return isinstance(func, ast.Attribute) and func.attr == "legacy"


def orphan_id_report(register_ids: frozenset[str], code_ids: frozenset[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    missing_in_register = sorted(code_ids - register_ids)
    unused_in_code = sorted(register_ids - code_ids)
    errors = tuple(f"legacy() id {i!r} used in code but missing from the register" for i in missing_in_register)
    warnings = tuple(f"{i}: non ancora collegati nel codice (nessuna chiamata legacy())" for i in unused_in_code)
    return errors, warnings


def _deref(node: dict, defs: dict) -> dict:
    if "$ref" in node:
        return defs.get(node["$ref"].rsplit("/", 1)[-1], {})
    if "allOf" in node and len(node["allOf"]) == 1:
        return _deref(node["allOf"][0], defs)
    return node


def _unwrap_container(node: dict, defs: dict) -> dict:
    """Unwrap an array (a path segment may name a column of a rows tuple) or an anyOf/oneOf union."""
    if node.get("type") == "array":
        return _deref(node.get("items", {}), defs)
    for key in ("anyOf", "oneOf"):
        for option in node.get(key, ()):
            resolved = _deref(option, defs)
            if resolved.get("properties") or resolved.get("type") == "array":
                return _unwrap_container(resolved, defs)
    return node


def _path_exists(schema: dict, defs: dict, path: str) -> bool:
    node = _deref(schema, defs)
    for part in path.split("."):
        node = _unwrap_container(node, defs)
        props = node.get("properties")
        if not props or part not in props:
            return False
        node = _deref(props[part], defs)
    return True


def run_checks(register: tuple[Divergence, ...], tools: dict[str, Tool], code_root: Path) -> CheckReport:
    orphan_errors, orphan_warnings = orphan_id_report(
        frozenset(d.id for d in register), legacy_ids_in_code(code_root)
    )
    errors = (
        unknown_tool_errors(register, frozenset(tools))
        + unknown_output_errors(register, tools)
        + duplicate_title_errors(register)
        + orphan_errors
    )
    warnings = empty_clausola_warnings(register) + orphan_warnings
    return CheckReport(errors=errors, warnings=warnings)


def main() -> None:
    report = run_checks(load_register(), discover(), REPO_SRC)
    for warning in report.warnings:
        print(f"WARNING: {warning}")
    for error in report.errors:
        print(f"ERROR: {error}")
    print(f"{len(report.errors)} errors, {len(report.warnings)} warnings")
    raise SystemExit(report.exit_code)


if __name__ == "__main__":
    main()
