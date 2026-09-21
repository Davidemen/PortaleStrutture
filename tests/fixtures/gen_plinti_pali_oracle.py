"""Generate the oracle fixture for `fond-plinto-su-pali` from `2xxxx_Plinti su pali_PL-FX_S&T
Eurocode 2.xlsx` (default sheet `Footing check`, 143k formulas).

The `reazioni` table itself (`Footing check!B6:I10639`) is never overridden: only scalar
geometry/material inputs change per case, so the Python side reuses the same
`plinti_pali_golden_rows.csv` table for every case (`apply_overrides` only touches scalars).
LibreOffice recalculates ~143k formulas per case (1-3 minutes): 3 cases only, per
docs/architecture-batch2.md §6. Run once: `uv run python tests/fixtures/gen_plinti_pali_oracle.py`.
"""
from pathlib import Path

from extract.fixtures import generate

READ = [
    "AF12", "AG12", "AV7", "AV36", "AZ13", "AZ14", "AV13", "AV14",  # Tool 1: envelope.
    "AV20", "AZ20", "AV28", "AZ28",  # Tool 2: bottom flexural design.
    "BG8", "BG9", "BG12", "BG19", "BG21", "BI22", "BL10", "BL13",  # Tool 3: strut + ties.
    "AR86", "AR96", "AR98", "AR99", "AR100", "AR103", "AR104",  # Tool 4: shear.
    "AR110", "AR111", "AR112",  # Tool 4: punching at the column face.
]

CASES = [
    # Case 0: spec golden case (docs/specs/fond-plinti-pali.md), no overrides.
    {},
    # Case 1: taller/narrower plinth, larger cover and assumed bar diameter, smaller av.
    {"AR8": 1400, "AR12": 60, "AR21": 2.5, "AR22": 2.5, "AR85": 28, "AR97": 350},
    # Case 2: different materials + column/pile dimensions (node/punching capacities change).
    {"AG6": 500, "AG7": 28, "AR58": 800, "AR59": 800, "AR107": 500},
]

if __name__ == "__main__":
    generate(
        "fond-plinti-pali",
        "Footing check",
        CASES,
        READ,
        Path(__file__).parent / "plinti_pali_oracle.json",
    )
