"""Regenerate tests/fixtures/sisma_vita_riferimento_oracle.json from sisma.xls[x], sheet Sisma.

Run with: uv run python tests/fixtures/gen_sisma_vita_riferimento.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {"I4": "Brembate", "I7": 50, "I8": "II"},  # spec §8 golden case, plus comune lookup
    {"I4": "Roma", "I7": 50, "I8": "III"},
    {"I7": 50, "I8": "I"},
    {"I7": 50, "I8": "IV"},
    {"I7": 10, "I8": "II"},
    {"I7": 100, "I8": "IV"},
]

READ = ["I5", "I6", "I9", "I10", "E13", "E14", "E15", "E16"]

if __name__ == "__main__":
    generate("sisma", "Sisma", CASES, READ, Path(__file__).parent / "sisma_vita_riferimento_oracle.json")
