"""Regenerate tests/fixtures/acciaio_incendio_proprieta_oracle.json from the workbook via
LibreOffice. `fuoco-materiali` has one sheet per θ (550/600/650/700 °C) that are the *same*
calculation at four fixed temperatures (docs/specs/small-units.md §"Purpose") — each sheet with
an empty override is a free golden case (docs/BUILD_CONTRACT.md §"Member tools").

Run with: uv run python tests/fixtures/gen_acciaio_incendio_proprieta.py
"""
import json
from pathlib import Path

from extract.fixtures import generate

READ = ["C20", "C21", "C22", "C23", "C24", "C25"]
SHEETS = ["550°C", "600°C", "650°C", "700°C"]

if __name__ == "__main__":
    target = Path(__file__).parent / "acciaio_incendio_proprieta_oracle.json"
    fixtures = []
    for sheet in SHEETS:
        [case] = generate("fuoco-materiali", sheet, cases=[{}], read=READ, target=target)
        fixtures = [*fixtures, {"sheet": sheet, **case}]
    target.write_text(json.dumps(fixtures, ensure_ascii=False, indent=1), encoding="utf-8")
