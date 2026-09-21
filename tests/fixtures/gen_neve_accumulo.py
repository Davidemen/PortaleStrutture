"""Regenerate tests/fixtures/neve_accumulo_oracle.json from the workbook via LibreOffice.

`accumulo`'s qsk2 branch reads `Neve!$H$9` (Bug 1, `docs/specs/neve.md` §7.1), so exercising it
needs the *other* sheet's altitude overridden too. `extract.fixtures.generate` only overrides one
sheet, so this script calls `extract.oracle.recalculate` directly with both sheets' overrides.

Run with: uv run python tests/fixtures/gen_neve_accumulo.py
"""
import json
from pathlib import Path

from openpyxl.utils.cell import coordinate_to_tuple

from extract.convert import to_xlsx
from extract.fixtures import workbook_path
from extract.oracle import recalculate

# Each case: 'H9' is this sheet's own altitude, 'neve_h9' is `Neve!H9` (Bug 1's cross-sheet source).
CASES = [
    {  # sanity: as>=200 -> bug3 selects qsk1, no cross-sheet contamination (matches spec §8 golden)
        "neve_h9": 249, "H9": 249, "H13": "Normale", "H26": 1,
        "H29": 43.15, "H30": 36.2, "H31": 10, "H32": 2, "H34": 0, "H35": 0.8, "H37": 0.45,
    },
    {  # as<200 -> bug3 selects qsk2, evaluated with Neve!H9=900 (Bug 1) instead of this sheet's 150
        "neve_h9": 900, "H9": 150, "H13": "Normale", "H26": 1,
        "H29": 43.15, "H30": 36.2, "H31": 10, "H32": 2, "H34": 0, "H35": 0.8, "H37": 0.45,
    },
    {  # b2(10) < ls(15): m1 interpolation branch (positive result)
        "neve_h9": 249, "H9": 249, "H13": "Normale", "H26": 1,
        "H29": 43.15, "H30": 10, "H31": 10, "H32": 2, "H34": 0, "H35": 0.8, "H37": 0.45,
    },
    {  # mw clamped to its lower bound 0.8
        "neve_h9": 249, "H9": 249, "H13": "Normale", "H26": 1,
        "H29": 1, "H30": 1, "H31": 50, "H32": 2, "H34": 0, "H35": 0.8, "H37": 0.45,
    },
    {  # mw clamped to its upper bound 4
        "neve_h9": 249, "H9": 249, "H13": "Normale", "H26": 1,
        "H29": 50, "H30": 50, "H31": 10, "H32": 20, "H34": 0, "H35": 0.8, "H37": 0.45,
    },
    {  # a>=15 -> ms nonzero
        "neve_h9": 249, "H9": 249, "H13": "Riparata", "H26": 1,
        "H29": 43.15, "H30": 36.2, "H31": 10, "H32": 2, "H34": 20, "H35": 0.8, "H37": 0.6,
    },
    {  # Ct != 1
        "neve_h9": 249, "H9": 249, "H13": "Battuta dai venti", "H26": 1.2,
        "H29": 43.15, "H30": 36.2, "H31": 10, "H32": 2, "H34": 0, "H35": 0.8, "H37": 0.45,
    },
    {  # as<200, own altitude equal to Neve!H9 (no visible contamination, sanity cross-check)
        "neve_h9": 180, "H9": 180, "H13": "Normale", "H26": 1,
        "H29": 43.15, "H30": 36.2, "H31": 10, "H32": 2, "H34": 0, "H35": 0.8, "H37": 0.45,
    },
]

READ = ["H8", "H10", "H14", "H33", "H36", "H38", "H39", "H43", "H44", "H45"]
COMUNE = "Bergamo"


def main() -> None:
    xlsx = to_xlsx(workbook_path("neve"))
    fixtures = []
    for case in CASES:
        neve_h9 = case["neve_h9"]
        accumulo_inputs = {"H5": COMUNE, **{k: v for k, v in case.items() if k != "neve_h9"}}
        values = recalculate(xlsx, {"Neve": {"H9": neve_h9}, "Neve accumulo": accumulo_inputs})
        outputs = {c: values["Neve accumulo"].get(coordinate_to_tuple(c)) for c in READ}
        fixtures = [*fixtures, {"inputs": {"neve_h9": neve_h9, **accumulo_inputs}, "outputs": outputs}]
    target = Path(__file__).parent / "neve_accumulo_oracle.json"
    target.write_text(json.dumps(fixtures, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
