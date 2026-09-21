"""Regenerate tests/fixtures/vento_cpe_oracle.json from the workbook via LibreOffice.

Run with: uv run python tests/fixtures/gen_vento_cpe.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {"D6": 15, "D7": 12, "D8": 9},  # golden: both squat, windward mid-segment
    {"D6": 10, "D7": 10, "D8": 60},  # both slender (h/d dir1=6, dir2=6) -> EDIFICIO SNELLO
    {"D6": 3, "D7": 30, "D8": 20},  # mixed: dir1 h/d=0.67 squat, dir2 h/d=6.67 slender -> DIR 2
    {"D6": 30, "D7": 3, "D8": 20},  # mixed: dir1 h/d=6.67 slender, dir2 h/d=0.67 squat -> DIR 1
    {"D6": 4, "D7": 4, "D8": 2},  # both h/d=0.5, side cpe at breakpoint
    {"D6": 4, "D7": 4, "D8": 4},  # both h/d=1, windward/leeward at breakpoint
    {"D6": 4, "D7": 4, "D8": 20},  # both h/d=5, exactly at slender threshold (still defined)
    {"D6": 4, "D7": 4, "D8": 0.4},  # both h/d=0.1, windward near zero segment
]

READ = ["D9", "E9", "B10", "D13", "E13", "D14", "E14", "D15", "E15"]

if __name__ == "__main__":
    generate("vento-cpe", "Foglio1", CASES, READ, Path(__file__).parent / "vento_cpe_oracle.json")
