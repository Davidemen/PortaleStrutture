"""CLAUDE.md rule 12 (JS modules <= 400 lines), enforced as a permanent test -- WORKBENCH_SPEC.md
§22 split `sketch-fit.js` for going over it. Checks `static/js` (the served UI) and, while an agent
is mid-refactor, `static_next/js` (the working copy, rule 3) if it exists."""
from pathlib import Path

MAX_LINES = 400
REPO_ROOT = Path(__file__).resolve().parents[2]


def _js_dirs() -> list[Path]:
    static_js = REPO_ROOT / "src" / "strutture" / "web" / "static" / "js"
    static_next_js = REPO_ROOT / "src" / "strutture" / "web" / "static_next" / "js"
    return [d for d in (static_js, static_next_js) if d.is_dir()]


def test_every_js_module_is_at_most_400_lines() -> None:
    oversized = []
    for js_dir in _js_dirs():
        for path in sorted(js_dir.glob("*.js")):
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > MAX_LINES:
                oversized.append(f"{path.relative_to(REPO_ROOT)}: {line_count} righe")
    assert not oversized, "moduli JS oltre il limite di 400 righe:\n" + "\n".join(oversized)
