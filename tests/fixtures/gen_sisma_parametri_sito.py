"""Regenerate tests/fixtures/sisma_parametri_sito_oracle.json from sisma.xls[x], sheet Sisma.

Run with: uv run python tests/fixtures/gen_sisma_parametri_sito.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {"I26": "A", "I27": "T1", "I28": 0.272, "I29": 2.436, "I30": 0.098},  # spec §8 golden inputs' sibling
    {"I26": "B", "I27": "T1", "I28": 0.272, "I29": 2.436, "I30": 0.098},  # golden case
    {"I26": "C", "I27": "T2", "I28": 0.35, "I29": 2.0, "I30": 0.15},
    {"I26": "D", "I27": "T3", "I28": 0.4, "I29": 2.2, "I30": 0.2},
    {"I26": "E", "I27": "T4", "I28": 0.3, "I29": 2.1, "I30": 0.12},
    {"I26": "B", "I27": "T1", "I28": 0.272, "I29": 2.5, "I30": 0.5},  # high F0*ag -> Ss(B) below 1.00
    {"I26": "C", "I27": "T1", "I28": 0.272, "I29": 1.0, "I30": 0.01},  # low F0*ag -> Ss upper clip
]

READ = ["I31", "I32", "I33", "I34", "I48", "I49", "I50"]

if __name__ == "__main__":
    generate("sisma", "Sisma", CASES, READ, Path(__file__).parent / "sisma_parametri_sito_oracle.json")
