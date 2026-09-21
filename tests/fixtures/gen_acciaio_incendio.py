"""Regenerate tests/fixtures/acciaio_incendio_resistenza_oracle.json from the workbook via
LibreOffice. Each case: {"D2": grade, "D3": elastic modulus}. Reads D4/D5 (base fy/fu, exercising
the D5 grade-selection bug for every grade) plus rows 9 (t=5min) and 32 (t=120min) for the
temperature/reduction-factor pipeline at both ends of the table.

Run with: uv run python tests/fixtures/gen_acciaio_incendio.py
"""
from pathlib import Path

from extract.fixtures import generate

READ = ["D4", "D5", "C9", "D9", "E9", "F9", "G9", "H9", "C32", "D32", "E32", "F32", "G32", "H32"]

CASES = [
    {"D2": "S235", "D3": 210000},  # correct 1st IF branch: fu=360
    {"D2": "S275", "D3": 210000},  # D5 bug branch — D3(=210000) never "s275" -> falls through to 510
    {"D2": "S355", "D3": 210000},  # fallback branch, correct by coincidence
    {"D2": "s235", "D3": 200000},  # case-insensitive grade match + a non-default elastic modulus
    {"D2": "s275", "D3": 195000},  # lower-case S275, exercises the bug again with another modulus
    {"D2": "s355", "D3": 210000},  # lower-case fallback branch
]

if __name__ == "__main__":
    generate(
        "acciaio-incendio",
        "Resistenza",
        cases=CASES,
        read=READ,
        target=Path(__file__).parent / "acciaio_incendio_resistenza_oracle.json",
    )
