"""Regenerate tests/fixtures/ca_pilastri_circolare_ntc2018_oracle.json from
`30_Calcolo pilastri in c.a. secondo NTC 2018 e Circolare2019.xls` (slug "ca-pilastri-ntc2018"),
sheet "Pilastri circolari" (docs/specs/ca-pilastri-ntc2018.md). Addresses confirmed directly
against build/cellmaps/ca-pilastri-ntc2018/pilastri-circolari.txt.

Run with: uv run python tests/fixtures/gen_ca_pilastri_circolare_ntc2018.py
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
    "Z8", "Z9", "H22", "H23", "H24", "J24", "H19", "H20", "H21", "CX38", "Z13",
    "Z15", "Z16", "Z17", "Y18", "Y20", "G26", "H27", "G28", "Z24", "Z25",
    "J60", "J62", "J63", "J64", "CX24",
    "J68", "L68", "J69", "L69", "J70", "L70", "J71", "L71", "J72", "L72",
]

if __name__ == "__main__":
    generate(
        "ca-pilastri-ntc2018", "Pilastri circolari", CASES, READ,
        Path(__file__).parent / "ca_pilastri_circolare_ntc2018_oracle.json",
    )
