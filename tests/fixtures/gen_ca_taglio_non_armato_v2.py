"""Regenerate tests/fixtures/ca_taglio_non_armato_v2_oracle.json from the `1m` sheet of the v2
workbook (per-metre-strip variant, direct fck + N°/Ø instead of Rck-derived fck + direct Asl).

Run with: uv run python tests/fixtures/gen_ca_taglio_non_armato_v2.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {"B2": 40, "B3": 32, "B7": 250, "B8": 68, "B9": 1000, "B11": 5, "B12": 12, "B14": 0},  # golden case
    {"B2": 25, "B3": 20.75, "B7": 300, "B8": 30, "B9": 300, "B11": 4, "B12": 12},  # small section, coherent fck/Rck
    {"B2": 30, "B3": 24.9, "B7": 150, "B8": 25, "B9": 250, "B11": 2, "B12": 12},  # d small -> k capped at 2
    {"B2": 40, "B3": 32, "B7": 250, "B8": 68, "B9": 1000, "B11": 5, "B12": 12, "B14": 100},  # NEd>0, sigma_cp below cap
    {"B2": 40, "B3": 32, "B7": 250, "B8": 68, "B9": 300, "B11": 5, "B12": 12, "B14": 500},  # NEd large -> sigma_cp hits 0.2*fcd cap
    {"B2": 30, "B3": 32, "B7": 600, "B8": 40, "B9": 1500, "B11": 20, "B12": 25},  # rho_l well above 0.02 (sheet never caps)
    {"B2": 35, "B3": 40, "B7": 800, "B8": 60, "B9": 400, "B11": 6, "B12": 16},  # large d -> VRd2 (vmin term) governs
    {"B2": 20, "B3": 16.6, "B7": 250, "B8": 30, "B9": 200, "B11": 3, "B12": 10, "B14": -300},  # NEd negative (tension)
]

READ = ["B4", "B10", "B13", "B15", "B17", "B18", "B19", "B21", "B22", "B23"]

if __name__ == "__main__":
    generate("ca-taglio-non-armato-v2", "1m", CASES, READ, Path(__file__).parent / "ca_taglio_non_armato_v2_oracle.json")
