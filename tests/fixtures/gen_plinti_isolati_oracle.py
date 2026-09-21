"""Generate the oracle fixture for `fond-plinto-isolato` from `2xxxx_Plinti isolati.xlsx`
(default sheet `INPUT`, results also read from `CHECKS` via multi-sheet addresses).

The reaction table itself (`LCC Reactions` -> `INPUT!A3:H541`) is never overridden: only the footing
geometry/material scalars change per case, so the Python side re-uses the same
`plinti_isolati_golden_rows.csv` table for every case (`apply_overrides` only touches scalars).
LibreOffice recalculates ~87k formulas per case (1-3 minutes): 4 cases only, per
docs/architecture-batch2.md §6. Run once: `uv run python tests/fixtures/gen_plinti_isolati_oracle.py`.
"""
from pathlib import Path

from extract.fixtures import generate

# Row-6 (first combo, ULS1) cells + Tool-2 aggregation cells (family ULS STR = rows 16 range) for
# every case; a geometry/material change shows up in both.
READ = [
    "CHECKS!C6", "CHECKS!D6", "CHECKS!E6", "CHECKS!F6", "CHECKS!G6", "CHECKS!H6", "CHECKS!I6",
    "CHECKS!K6", "CHECKS!L6", "CHECKS!M6", "CHECKS!N6", "CHECKS!S6", "CHECKS!T6", "CHECKS!Z6",
    "CHECKS!AA6", "CHECKS!AC6", "CHECKS!AD6", "CHECKS!AE6", "CHECKS!AF6", "CHECKS!AG6", "CHECKS!AH6",
    "CHECKS!AJ6", "CHECKS!AL6", "CHECKS!AM6", "CHECKS!AO6", "CHECKS!AP6",
    "L16", "N16", "P16", "R16", "T5", "T7", "T8",
    "T13", "T14", "T15", "T16", "T17", "T18", "T19", "T20", "T21", "T22", "T23", "T24", "T25",
    "T30", "U30", "T31", "U31",
]

CASES = [
    # Case 0: spec golden case (docs/specs/fond-plinti-isolati.md), no overrides.
    {},
    # Case 1: larger plinth plan + a pedestal (weights, moment lever arm, cantilever length change).
    {"P3": 6000, "P4": 5000, "P7": 1000, "P8": 1000, "P9": 500, "P10": 300},
    # Case 2: different soil unit weight/friction + haunch offset (self-weight, sliding, lever arm).
    {"P34": 18, "P35": 22, "P11": 150},
    # Case 3: different materials + rebar spacing/cover/manual diameter (flexural design chain).
    {"T3": 450, "T6": 40, "T11": 15, "T12": 5, "T22": 16, "T24": 16},
]

if __name__ == "__main__":
    generate(
        "fond-plinti-isolati",
        "INPUT",
        CASES,
        READ,
        Path(__file__).parent / "plinti_isolati_oracle.json",
    )
