"""Regenerate tests/fixtures/sisma_fattori_struttura_oracle.json from sisma.xls[x], sheet Sisma.

Run with: uv run python tests/fixtures/gen_sisma_fattori_struttura.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {"I25": "SLO", "I37": 5, "I39": 1.5, "I40": "SI", "I44": 1.5},  # SLE: q must stay 1
    {"I25": "SLD", "I37": 5, "I39": 1.5, "I40": "SI", "I44": 1.5},  # SLE: q must stay 1
    {"I25": "SLV", "I37": 5, "I39": 1.5, "I40": "SI", "I44": 1.5},  # spec §8 golden: q=q0
    {"I25": "SLV", "I37": 5, "I39": 1.5, "I40": "NO", "I44": 1.5},  # ULS, irregular: q=q0*0.8
    {"I25": "SLC", "I37": 10, "I39": 3.0, "I40": "SI", "I44": 2.0},  # different damping/q0
    # case-insensitivity of the sheet's own I25="slv"/I40="si" literal compares (Sisma!N25/I41)
    {"I25": "slv", "I37": 5, "I39": 1.5, "I40": "si", "I44": 1.5},
]

READ = ["N25", "I38", "I41"]

if __name__ == "__main__":
    generate("sisma", "Sisma", CASES, READ, Path(__file__).parent / "sisma_fattori_struttura_oracle.json")
