"""Regenerate tests/fixtures/vento_pressione_oracle.json from the workbook via LibreOffice.

Unlike `extract.fixtures.generate` (single-sheet reads), this tool's outputs span two sheets:
scalar results on `Vento`, the pressure profile on `Tabelle!K4:Q1004`. Each case overrides only
`Vento` input cells (Tabelle!M1 stays at its default 1000 sections) and reads back a handful of
profile rows by section index `n` (row = n+4), matching spec §8's z=zmin/10/25/H sample points.

Run with: PYTHONPATH=. uv run python tests/fixtures/gen_vento_pressione.py
"""
import json
from pathlib import Path

from openpyxl.utils.cell import coordinate_to_tuple

from extract.convert import to_xlsx
from extract.fixtures import workbook_path
from extract.oracle import recalculate

VENTO_READ = ["H5", "H6", "H7", "B10", "E10", "H10", "H12", "H14", "H15", "B31", "E31", "H31", "H36", "H37"]
TABELLE_ROW_COLS = ["L", "O", "P"]  # height, sqrt(ce), qz = qb*ce
SEZIONI_LETTE = (0, 500, 1000)  # bottom (z<zmin branch), mid-height, top (z=H, cross-checks H36*H37)

CASES = [
    # golden case (spec §8): zona 1, TR=50, categoria II, ct=1
    {"H4": "Milano", "H8": 120, "H13": 50, "H29": "II", "H33": 1, "H34": 60},
    # zona 2, altitude above a0=750 -> exercises the altitude-correction branch of vref
    {"H4": "Bologna", "H8": 1200, "H13": 50, "H29": "III", "H33": 1, "H34": 30},
    # zona 3, H < zmin(I)=2 -> whole building below zmin, TR != 50
    {"H4": "Chieti", "H8": 50, "H13": 100, "H29": "I", "H33": 1, "H34": 1},
    # zona 4, ct != 1, TR < 50
    {"H4": "Reggio di Calabria", "H8": 10, "H13": 10, "H29": "IV", "H33": 1.2, "H34": 45},
    # zona 5, TR > 50, categoria V (largest zmin)
    {"H4": "Oristano", "H8": 5, "H13": 200, "H29": "V", "H33": 1, "H34": 100},
    # zona 7, altitude far above a0=1000
    {"H4": "Genova", "H8": 2000, "H13": 50, "H29": "II", "H33": 1, "H34": 15},
    # zona 8, ct < 1
    {"H4": "Trieste", "H8": 0, "H13": 50, "H29": "III", "H33": 0.9, "H34": 8},
    # zona 6, H == zmin(II)=4 boundary, short TR
    {"H4": "Cagliari", "H8": 300, "H13": 2, "H29": "II", "H33": 1, "H34": 4},
]


def _tabelle_row(values: dict[str, dict[tuple[int, int], object]], n: int) -> dict[str, object]:
    row = n + 4
    tabelle = values.get("Tabelle", {})
    return {"n": n, **{col: tabelle.get(coordinate_to_tuple(f"{col}{row}")) for col in TABELLE_ROW_COLS}}


def _case_fixture(xlsx: Path, inputs: dict[str, object]) -> dict[str, object]:
    values = recalculate(xlsx, {"Vento": inputs})
    vento = values.get("Vento", {})
    return {
        "inputs": inputs,
        "vento": {c: vento.get(coordinate_to_tuple(c)) for c in VENTO_READ},
        "tabelle": [_tabelle_row(values, n) for n in SEZIONI_LETTE],
    }


def generate() -> list[dict]:
    xlsx = to_xlsx(workbook_path("vento"))
    return [_case_fixture(xlsx, inputs) for inputs in CASES]


if __name__ == "__main__":
    target = Path(__file__).parent / "vento_pressione_oracle.json"
    target.write_text(json.dumps(generate(), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {target}")
