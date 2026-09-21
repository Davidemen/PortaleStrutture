"""Filter coverage findings down to cells a unit's spec never mentions (zero-token gap list).

Usage: python -m extract.spec_gaps build/specs.json build/coverage.json
"""
import json
import re
import sys
from pathlib import Path

from openpyxl.utils import get_column_letter, range_boundaries

RANGE_PATTERN = re.compile(r"\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?")
MAX_RANGE_CELLS = 20000
GAP_KINDS = ("missing_cells", "unaccounted_leaves", "unused_inputs", "candidate_outputs")


def mentioned_coords(spec_text: str) -> frozenset[str]:
    """Every cell address the spec names, with ranges expanded."""
    coords: set[str] = set()
    for match in RANGE_PATTERN.finditer(spec_text):
        min_col, min_row, max_col, max_row = range_boundaries(match.group(0).replace("$", ""))
        if (max_col - min_col + 1) * (max_row - min_row + 1) <= MAX_RANGE_CELLS:
            coords.update(f"{get_column_letter(c)}{r}" for r in range(min_row, max_row + 1) for c in range(min_col, max_col + 1))
    return frozenset(coords)


def coord_of(label: str) -> str:
    return label.split("!", 1)[1].split("=", 1)[0]


def unit_gaps(unit: dict, findings: dict[str, dict]) -> dict:
    known = mentioned_coords(Path(unit["specPath"]).read_text(encoding="utf-8"))
    results = [findings[t["name"]] for t in unit["tools"] if t["name"] in findings]
    gaps = {
        kind: sorted({label for r in results for label in r.get(kind, []) if kind != "unaccounted_leaves" and kind != "candidate_outputs" or coord_of(label) not in known})
        for kind in GAP_KINDS
    }
    errors = [f"{r['tool']}: {r['error']}" for r in results if "error" in r]
    return {"unit": unit["unit"].split()[0], "specPath": unit["specPath"], **gaps, "errors": errors}


def main(specs_path: str, coverage_path: str) -> int:
    specs = json.loads(Path(specs_path).read_text(encoding="utf-8"))
    findings = {r["tool"]: r for r in json.loads(Path(coverage_path).read_text(encoding="utf-8"))}
    print(json.dumps([unit_gaps(u, findings) for u in specs], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
