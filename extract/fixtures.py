"""Generate oracle fixtures: recalculate a workbook with LibreOffice for several input sets.

    from extract.fixtures import generate
    generate("neve", "Neve", cases=[{"H9": 350, "H26": "Normale"}], read=["H10", "H14"],
             target=Path("tests/fixtures/neve_carico_falda_oracle.json"))

Each fixture entry is {"inputs": {coord: value}, "outputs": {coord: value}}. Tests read the JSON;
LibreOffice is only needed when (re)generating.
"""
import json
from pathlib import Path

from openpyxl.utils.cell import coordinate_to_tuple

from .config import workbook_slug, workbook_sources
from .convert import to_xlsx
from .oracle import recalculate


def workbook_path(slug: str) -> Path:
    matches = [p for p in workbook_sources() if workbook_slug(p) == slug]
    if len(matches) != 1:
        raise FileNotFoundError(f"expected exactly one workbook for slug {slug!r}, found {len(matches)}")
    return matches[0]


def split_address(address: str, default_sheet: str) -> tuple[str, str]:
    """'H6' -> (default sheet, 'H6'); "CHECKS!AA6" or "'LC Reactions'!C4" -> (that sheet, cell)."""
    if "!" not in address:
        return default_sheet, address
    sheet, cell = address.rsplit("!", 1)
    return sheet.strip("'"), cell


def split_overrides(inputs: dict[str, object], default_sheet: str) -> dict[str, dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for address, value in inputs.items():
        sheet, cell = split_address(address, default_sheet)
        grouped = {**grouped, sheet: {**grouped.get(sheet, {}), cell: value}}
    return grouped


def generate(slug: str, sheet: str, cases: list[dict[str, object]], read: list[str], target: Path) -> list[dict]:
    """Run every case through LibreOffice and write the fixture file. `sheet` is the default Excel sheet;
    any input or read address may name another one ("CHECKS!AA6")."""
    xlsx = to_xlsx(workbook_path(slug))
    fixtures = []
    for inputs in cases:
        values = recalculate(xlsx, split_overrides(inputs, sheet) if inputs else None)
        outputs = {}
        for address in read:
            read_sheet, cell = split_address(address, sheet)
            outputs = {**outputs, address: values.get(read_sheet, {}).get(coordinate_to_tuple(cell))}
        fixtures = [*fixtures, {"inputs": inputs, "outputs": outputs}]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(fixtures, ensure_ascii=False, indent=1), encoding="utf-8")
    return fixtures
