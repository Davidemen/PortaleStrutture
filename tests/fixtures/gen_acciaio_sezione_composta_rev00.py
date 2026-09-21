"""Free extra golden case: `Rev00` is the superseded sheet, same default inputs as `Rev01` but
without the O/P (Iy reinforced/base) columns — read only the quantities both sheets compute.

Run with: uv run python tests/fixtures/gen_acciaio_sezione_composta_rev00.py
"""
from pathlib import Path

from extract.fixtures import generate

READ = ["B1", "B2", "B6", "C6", "B7", "B9", "C9", "B10", "C10", "G6", "H6", "M13", "N13"]

if __name__ == "__main__":
    generate(
        "acciaio-sezione-h-rimpiattata",
        "Rev00",
        cases=[{}],
        read=READ,
        target=Path(__file__).parent / "acciaio_sezione_composta_rev00_oracle.json",
    )
