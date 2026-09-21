"""Regenerate tests/fixtures/ca_pilastri_rettangolare_oracle.json from ca-pilastri.xls, sheet
"Pilastri rettangolari".

Run with: uv run python tests/fixtures/gen_ca_pilastri_rettangolare.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {},  # golden (cached sheet defaults)
    {"H14": 20, "H15": 25},  # rs too high -> J23 "NO" (upper bound)
    {"H14": 4, "H15": 12},  # rs too low -> J23 "NO" (lower bound)
    {"H10": 400},  # sigma_cp < 0.25*fcd -> ac branch 1
    {"H10": 800},  # 0.25*fcd <= sigma_cp < 0.5*fcd -> ac branch 2
    {"H16": 24, "H17": 150},  # cotTheta raw < 1 -> clamped to 1
    {"H16": 16, "H17": 150},  # cotTheta raw in [1, 2.5] -> not clamped
    {"H7": 1000},  # hcr: H < 3*L1 branch
    {"H8": "FeB38k", "H9": "C40/50", "H16": 12, "H17": 100},  # other steel/concrete grade
    {"H8": "FeB22k", "H9": "C50/60", "H14": 12, "H15": 20},  # another steel/concrete grade
]

READ = [
    "Z8", "Z9", "H21", "H22", "H23", "J23", "H18", "H19", "H20", "CX38", "Z13",
    "Z15", "Z16", "Z17", "Y18", "Y20", "G25", "H26", "G27", "Z24", "Z25",
    "J53", "J55", "J56", "J57", "CX24",
    "J60", "L60", "J61", "L61", "J62", "L62", "J63", "L63", "J64", "L64",
]

if __name__ == "__main__":
    generate("ca-pilastri", "Pilastri rettangolari", CASES, READ, Path(__file__).parent / "ca_pilastri_rettangolare_oracle.json")
