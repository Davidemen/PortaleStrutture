"""Regenerate tests/fixtures/ca_pilastri_rettangolare_ntc2018_oracle.json from
`30_Calcolo pilastri in c.a. secondo NTC 2018 e Circolare2019.xls` (slug "ca-pilastri-ntc2018"),
sheet "Pilastri rettangolari" (docs/specs/ca-pilastri-ntc2018.md). Addresses confirmed directly
against build/cellmaps/ca-pilastri-ntc2018/pilastri-rettangolari.txt (some differ from the delta
spec's own "+1 row" prose, e.g. the detailing block is J61-J65, not J60-J64).

Run with: uv run python tests/fixtures/gen_ca_pilastri_rettangolare_ntc2018.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {},  # golden (cached sheet defaults)
    {"H15": 20, "H16": 25},  # rs too high -> J24 "NO" (4%-ceiling-only check)
    {"H11": 400},  # sigma_cp < 0.25*fcd -> ac branch 1
    {"H17": 24, "H18": 150},  # cotTheta raw < 1 -> clamped to 1
    {"H8": 1000},  # hcr: H < 3*L1 branch
]

READ = [
    "Z8", "Z9", "H22", "H23", "H24", "J24", "H19", "H20", "H21", "CX38", "Z13",
    "Z15", "Z16", "Z17", "Y18", "Y20", "G26", "H27", "G28", "Z24", "Z25",
    "J53", "J55", "J56", "J57", "CX24",
    "J61", "L61", "J62", "L62", "J63", "L63", "J64", "L64", "J65", "L65",
]

if __name__ == "__main__":
    generate(
        "ca-pilastri-ntc2018", "Pilastri rettangolari", CASES, READ,
        Path(__file__).parent / "ca_pilastri_rettangolare_ntc2018_oracle.json",
    )
