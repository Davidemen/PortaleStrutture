"""Regenerate tests/fixtures/acciaio_sezione_composta_oracle.json from the workbook via
LibreOffice (sheet `Rev01`). Each case overrides the profile/plate input cells; `C9`/`C10` (plate
height, sheet formulas `=C7+3.5+3.5`) are read back so the Python model — where plate height is a
free input, not a derived cell — can be given the sheet's own computed value.

`B9` is always kept equal to `C6` (flange thickness) across cases: the sheet's bottom-flange
centroid formula `F8=B9/2` is a fragile reference to the first plate's thickness instead of the
true flange half-thickness (harmless only when they coincide, see docs/divergences — flagged
"Da verificare", not reproduced by this port, which always uses the true `tf/2`).

Run with: uv run python tests/fixtures/gen_acciaio_sezione_composta.py
"""
from pathlib import Path

from extract.fixtures import generate

READ = ["B1", "B2", "B6", "C6", "B7", "B9", "C9", "B10", "C10", "G6", "H6", "M13", "N13", "O13", "P13"]

CASES = [
    {},  # sheet default: HEA120-like profile + one active plate (B10=0 disables the second)
    {"B10": 8},  # both plates active, same width — exercises the H6 yN bug with a nonzero last row
    {"B9": 0, "B10": 0},  # unreinforced profile: reinforced quantities must equal the base ones
    {"B7": 6},  # thicker web
    {"B7": 3, "C6": 3, "B9": 3},  # thin flange/web/plate
    {"B1": 160, "B2": 140, "B6": 140, "C6": 10, "B7": 6, "B9": 10, "B10": 10},  # larger section, both plates
    {"B1": 200, "B2": 100, "B6": 100, "C6": 6, "B7": 4, "B9": 6},  # slender asymmetric-looking profile, one plate
    {"B1": 90, "B2": 80, "B6": 80, "C6": 6, "B7": 4, "B9": 6, "B10": 6},  # small section, both plates active
]

if __name__ == "__main__":
    generate(
        "acciaio-sezione-h-rimpiattata",
        "Rev01",
        cases=CASES,
        read=READ,
        target=Path(__file__).parent / "acciaio_sezione_composta_oracle.json",
    )
