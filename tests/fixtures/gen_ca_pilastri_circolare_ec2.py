"""Regenerate tests/fixtures/ca_pilastri_circolare_ec2_oracle.json from
`31_Calcolo pilastri in c.a. secondo UNI EN 1992-1-1 2005.xls` (slug "ca-pilastri-ec2"), sheet
"Circolari_UNI EN 1992-1-1 2005" (docs/specs/ca-pilastri-ec2.md). Main-flow input cells (H6, H8-H18,
H25) are the same addresses as the NTC2018 circular sheet. Addresses confirmed directly against
build/cellmaps/ca-pilastri-ec2/circolari-uni-en-1992-1-1-2005.txt (note: the mechanical
reinforcement ratio ω lives at `DB49` here, not `CX49` as in the rectangular sheet).

Run with: uv run python tests/fixtures/gen_ca_pilastri_circolare_ec2.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {},  # golden (cached sheet defaults; rs=0.04 -> J24 "NO", exact upper boundary)
    {"H15": 8},  # rs clearly passing
    {"H11": 300},  # sigma_cp < 0.25*fcd -> ac branch 1
    {"H17": 18, "H18": 150},  # cotTheta raw < 1 -> clamped to 1
    {"H8": 800},  # hcr: H < 3*D branch
]

READ = [
    "Z8", "Z9", "H22", "H23", "H24", "J24", "H19", "H20", "H21", "CX38", "CX28", "Z13",
    "Z15", "Z16", "Z17", "Y18", "Y20", "G26", "H27", "G28", "Z24", "Z25", "DB49",
    "J61", "J63", "J64", "J65", "J66", "CX24",
    "J69", "L69", "J70", "L70", "J71", "L71", "J72", "L72", "J73", "L73",
]

if __name__ == "__main__":
    generate(
        "ca-pilastri-ec2", "Circolari_UNI EN 1992-1-1 2005", CASES, READ,
        Path(__file__).parent / "ca_pilastri_circolare_ec2_oracle.json",
    )
