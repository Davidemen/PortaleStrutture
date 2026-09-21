"""Regenerate tests/fixtures/sisma_spettro_oracle.json from sisma.xls[x], sheet Sisma.

Reads (T, Se, Sd) at representative rows across all four spectrum branches (Sisma!I55:J149):
row55=T0 (ramp start, sheet's own undivided-J55 quirk), row56=TB, row57=TC, row58 (TC<T<TD decay),
row90=TD (breakpoint), row94/row107 (T>=TD decay), row149=T5 (hardcoded last point).

Run with: uv run python tests/fixtures/gen_sisma_spettro.py
"""
from pathlib import Path

from extract.fixtures import generate

ROWS = (55, 56, 57, 58, 90, 94, 107, 149)
READ = [f"{col}{row}" for row in ROWS for col in ("I", "J")]

CASES = [
    # golden case: SLV (ULS, divides by q)
    {"I25": "SLV", "I26": "B", "I27": "T1", "I28": 0.272, "I29": 2.436, "I30": 0.098, "I37": 5, "I39": 1.5, "I40": "SI"},
    # SLO (SLE, undivided elastic spectrum for every row, including row55)
    {"I25": "SLO", "I26": "B", "I27": "T1", "I28": 0.272, "I29": 2.436, "I30": 0.098, "I37": 5, "I39": 1.5, "I40": "SI"},
    # SLC, different soil/kr/damping to exercise a distinct branch shape
    {"I25": "SLC", "I26": "D", "I27": "T3", "I28": 0.4, "I29": 2.2, "I30": 0.2, "I37": 8, "I39": 3.0, "I40": "NO"},
]

if __name__ == "__main__":
    generate("sisma", "Sisma", CASES, READ, Path(__file__).parent / "sisma_spettro_oracle.json")
