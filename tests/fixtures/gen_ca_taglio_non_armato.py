"""Regenerate tests/fixtures/ca_taglio_non_armato_oracle.json from the workbook via LibreOffice.

Run with: uv run python tests/fixtures/gen_ca_taglio_non_armato.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {"B2": 35, "B7": 500, "B8": 50, "B9": 1000, "B11": 1005, "B12": 0},  # golden case
    {"B2": 25, "B7": 300, "B8": 30, "B9": 300, "B11": 452, "B12": 0},  # small d -> k close to cap but < 2
    {"B2": 30, "B7": 150, "B8": 25, "B9": 250, "B11": 226, "B12": 0},  # d=125mm -> k=1+sqrt(200/125)>2 -> k capped at 2
    {"B2": 35, "B7": 500, "B8": 50, "B9": 1000, "B11": 1005, "B12": 500},  # NEd>0, sigma_cp below cap
    {"B2": 35, "B7": 500, "B8": 50, "B9": 300, "B11": 1005, "B12": 2000},  # NEd large -> sigma_cp hits 0.2*fcd cap
    {"B2": 30, "B7": 600, "B8": 40, "B9": 1500, "B11": 25000, "B12": 0},  # rho_l = 25000/(1500*560)=0.0298 > 0.02 (uncapped in sheet)
    {"B2": 40, "B7": 800, "B8": 60, "B9": 400, "B11": 2500, "B12": 0},  # large d -> VRd2 (vmin term) governs
    {"B2": 20, "B7": 250, "B8": 30, "B9": 200, "B11": 157, "B12": -300},  # NEd negative (tension) -> sigma_cp negative
]

READ = ["B3", "B4", "B10", "B13", "B15", "B16", "B17", "B19", "B20", "B21"]

if __name__ == "__main__":
    generate("ca-taglio-non-armato", "Foglio1", CASES, READ, Path(__file__).parent / "ca_taglio_non_armato_oracle.json")
