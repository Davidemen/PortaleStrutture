"""Regenerate tests/fixtures/ca_pilastri_rettangolare_ec2_oracle.json from
`31_Calcolo pilastri in c.a. secondo UNI EN 1992-1-1 2005.xls` (slug "ca-pilastri-ec2"), sheet
"Ret._UNI EN 1992-1-1 2005" (docs/specs/ca-pilastri-ec2.md). Main-flow input cells (H6-H18, H25)
are the same addresses as the NTC2018 sheet; outputs differ (extra CX28/CX49 rows, a "quater"
detailing check for the max reinforcement ratio). Addresses confirmed directly against
build/cellmaps/ca-pilastri-ec2/ret-uni-en-1992-1-1-2005.txt.

Run with: uv run python tests/fixtures/gen_ca_pilastri_rettangolare_ec2.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {},  # golden (cached sheet defaults)
    {"H15": 20, "H16": 25},  # rs too high -> J24 "NO" / area massima "NO"
    {"H11": 400},  # sigma_cp < 0.25*fcd -> ac branch 1
    {"H17": 24, "H18": 150},  # cotTheta raw < 1 -> clamped to 1
    {"H8": 1000},  # hcr: H < 3*L1 branch
]

READ = [
    "Z8", "Z9", "H22", "H23", "H24", "J24", "H19", "H20", "H21", "CX38", "CX28", "Z13",
    "Z15", "Z16", "Z17", "Y18", "Y20", "G26", "H27", "G28", "Z24", "Z25", "CX49",
    "J54", "J56", "J57", "J58", "J59", "CX24",
    "J62", "L62", "J63", "L63", "J64", "L64", "J65", "L65", "J66", "L66",
]

if __name__ == "__main__":
    generate(
        "ca-pilastri-ec2", "Ret._UNI EN 1992-1-1 2005", CASES, READ,
        Path(__file__).parent / "ca_pilastri_rettangolare_ec2_oracle.json",
    )
