"""Dumps every tool example's sketch views to tests/fixtures/sketch_viste.json (dev tool, not
production code): one entry per (tool, mode) whose example has a `schizzo`, keyed
`"<tool.name>#standard"` / `"<tool.name>#excel"` (both modes when the model has `legacy_compat`).
Used by tests/e2e/sketch_fit.test.mjs as a characterisation fixture for the WORKBENCH_SPEC.md
§22 `sketch-fit.js` split: run once BEFORE moving code, never at test time.
"""
import json
from pathlib import Path
from typing import Any

from strutture.shared.tool import discover, execute

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sketch_viste.json"


def _viste_for(tool: Any, legacy_compat: bool) -> list[dict[str, Any]] | None:
    if tool.example is None:
        return None
    raw = {**tool.example, "legacy_compat": legacy_compat} if "legacy_compat" in tool.input_model.model_fields else tool.example
    report = execute(tool, raw)
    if not report.ok:
        return None
    schizzo = getattr(report.data, "schizzo", None)
    if schizzo is None:
        return None
    return [vista.model_dump(mode="json") for vista in schizzo.viste]


def main() -> None:
    tools = discover()
    fixture: dict[str, list[dict[str, Any]]] = {}
    for tool in sorted(tools.values(), key=lambda t: t.name):
        has_legacy = "legacy_compat" in tool.input_model.model_fields
        modes = (False, True) if has_legacy else (False,)
        for legacy_compat in modes:
            viste = _viste_for(tool, legacy_compat)
            if viste:
                suffix = "excel" if legacy_compat else "standard"
                fixture[f"{tool.name}#{suffix}"] = viste
    FIXTURE_PATH.write_text(
        json.dumps(fixture, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(fixture)} entries to {FIXTURE_PATH}")


if __name__ == "__main__":
    main()
