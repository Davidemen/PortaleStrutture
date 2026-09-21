"""Regenerate tests/fixtures/ca_pilastri_circolare_oracle.json from ca-pilastri.xls, sheet
"Pilastri circolari".

Run with: uv run python tests/fixtures/gen_ca_pilastri_circolare.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {},  # golden (cached sheet defaults; rs=0.04 -> J23 "NO", exact upper boundary)
    {"H14": 8},  # rs clearly passing
    {"H14": 4, "H15": 12},  # rs too low -> "NO" (lower bound)
    {"H10": 300},  # sigma_cp < 0.25*fcd -> ac branch 1
    {"H10": 700},  # 0.25*fcd <= sigma_cp < 0.5*fcd -> ac branch 2
    {"H16": 18, "H17": 150},  # cotTheta raw < 1 -> clamped to 1
    {"H16": 6, "H17": 300},  # cotTheta raw > 2.5 -> clamped to 2.5
    {"H7": 800},  # hcr: H < 3*D branch
    {"H8": "FeB38k", "H9": "C40/50", "H16": 12, "H17": 100},  # other steel/concrete grade
    {"H8": "FeB22k", "H9": "C50/60", "H14": 12, "H15": 20},  # another steel/concrete grade
]

READ = [
    "Z8", "Z9", "H21", "H22", "H23", "J23", "H18", "H19", "H20", "CX38", "Z13",
    "Z15", "Z16", "Z17", "Y18", "Y20", "G25", "H26", "G27", "Z24", "Z25",
    "J60", "J62", "J63", "J64", "CX24",
    "J67", "L67", "J68", "L68", "J69", "L69", "J70", "L70", "J71", "L71",
]

if __name__ == "__main__":
    generate("ca-pilastri", "Pilastri circolari", CASES, READ, Path(__file__).parent / "ca_pilastri_circolare_oracle.json")
