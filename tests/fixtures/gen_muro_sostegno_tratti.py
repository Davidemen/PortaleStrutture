"""Regenerate tests/fixtures/muro_sostegno_tratti_oracle.json — free extra golden cases from
sheets "Tratto B".."Tratto E" of `Muro di sostegno DM2018.xlsx` (each sheet's own cached
input/output values, empty override; see docs/BUILD_CONTRACT.md "Extra golden cases").

Run with: uv run python tests/fixtures/gen_muro_sostegno_tratti.py
"""
from pathlib import Path

from extract.fixtures import generate

SHEETS = ["Tratto B", "Tratto C", "Tratto D", "Tratto E"]

INPUT_CELLS = [
    "I4", "I5", "I6", "I7", "I8", "I9", "I10", "I15", "I16", "I17", "I18", "I19",
    "I21", "I22", "I25", "I26", "I27", "I28", "I29", "I31", "I32", "I38",
]
_TOOL1_COLS = ["G", "I", "K", "M", "Q", "S"]
_TOOL1_SISMA_EXTRA = ["Y", "Z", "AA"]
_TOOL2_COLS = ["B", "M", "N", "O", "Q", "R", "S"]
_TOOL3_COLS = ["D", "E", "G", "H", "M", "N", "O", "Q", "R", "S"]

READ = list(INPUT_CELLS) + ["H151", "I151", "K169", "M169", "M187", "N187"]
for tool1_row, tool2_row, tool3_row, sismica in [(45, 56, 67, False), (46, 57, 68, False), (47, 58, 69, False), (80, 87, 94, True), (81, 88, 95, True)]:
    READ += [f"{col}{tool1_row}" for col in _TOOL1_COLS]
    if sismica:
        READ += [f"{col}{tool1_row}" for col in _TOOL1_SISMA_EXTRA]
    READ += [f"{col}{tool2_row}" for col in _TOOL2_COLS]
    READ += [f"{col}{tool3_row}" for col in _TOOL3_COLS]

if __name__ == "__main__":
    fixtures = []
    for sheet in SHEETS:
        [entry] = generate("muro-sostegno", sheet, [{}], READ, Path(__file__).parent / "_tmp_muro_tratti.json")
        fixtures.append({"sheet": sheet, "outputs": entry["outputs"]})
    target = Path(__file__).parent / "muro_sostegno_tratti_oracle.json"
    target.write_text(__import__("json").dumps(fixtures, ensure_ascii=False, indent=1), encoding="utf-8")
    (Path(__file__).parent / "_tmp_muro_tratti.json").unlink(missing_ok=True)
