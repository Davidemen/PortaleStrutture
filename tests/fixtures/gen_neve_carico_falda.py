"""Regenerate tests/fixtures/neve_carico_falda_oracle.json from the workbook via LibreOffice.

Run with: uv run python tests/fixtures/gen_neve_carico_falda.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {"H5": "Mapello", "H9": 250, "H13": "Normale", "H26": 1, "H30": 0, "H31": "NO", "H52": 35, "H53": "NO", "H56": 50, "H57": "NO"},  # golden
    {"H5": "Brembate", "H9": 150, "H13": "Riparata", "H26": 1, "H30": 10, "H31": "NO", "H52": 10, "H53": "NO", "H56": 10, "H57": "NO"},  # as<200 branch, zona II
    {"H5": "Milano", "H9": 400, "H13": "Battuta dai venti", "H26": 1, "H30": 25, "H31": "NO", "H52": 25, "H53": "NO", "H56": 25, "H57": "NO"},  # as>=200
    {"H5": "Mapello", "H9": 250, "H13": "Normale", "H26": 1, "H30": 30, "H31": "NO", "H52": 30, "H53": "NO", "H56": 30, "H57": "NO"},  # alpha=30 boundary
    {"H5": "Mapello", "H9": 250, "H13": "Normale", "H26": 1, "H30": 60, "H31": "NO", "H52": 60, "H53": "NO", "H56": 60, "H57": "NO"},  # alpha=60 boundary
    {"H5": "Mapello", "H9": 250, "H13": "Normale", "H26": 1, "H30": 45, "H31": "SI", "H52": 45, "H53": "SI", "H56": 45, "H57": "SI"},  # parapetto SI overrides angle
    {"H5": "Mapello", "H9": 250, "H13": "Normale", "H26": 1, "H30": 70, "H31": "NO", "H52": 70, "H53": "NO", "H56": 70, "H57": "NO"},  # >=60 -> mu=0
    {"H5": "Mapello", "H9": 250, "H13": "Normale", "H26": 1.2, "H30": 15, "H31": "NO", "H52": 15, "H53": "NO", "H56": 15, "H57": "NO"},  # Ct != 1
]

READ = ["H6", "H7", "H8", "H10", "H14", "H32", "D34", "H54", "D60", "H58", "H61"]

if __name__ == "__main__":
    generate("neve", "Neve", CASES, READ, Path(__file__).parent / "neve_carico_falda_oracle.json")
