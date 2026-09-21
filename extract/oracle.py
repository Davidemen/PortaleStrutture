"""LibreOffice as a recalculation oracle for differential tests.

recalculate() saves the workbook through openpyxl (which drops cached values, forcing
LibreOffice to compute every formula on load), applies input overrides, converts it
headless, and reads back the computed values.

Usage: python -m extract.oracle      # validate: hard-recalc every workbook, compare to Excel's values
"""
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import openpyxl

from .cells import cached_values, load_sheets
from .config import workbook_slug, workbook_sources
from .convert import CONVERT_TIMEOUT_S, find_soffice, profile_argument, to_xlsx

ORACLE_REL_TOL = 1e-6
MAX_SHOWN = 5
# A workbook saved by an Excel without XLOOKUP & co. stores them as add-in / user-defined calls,
# which every engine evaluates to #NAME?; the standard future-function prefix restores them.
UNKNOWN_FUNCTION_PREFIX = re.compile(r"_xl(?:l|udf)\.(?=[A-Z][A-Z0-9.]*\()")
Values = dict[str, dict[tuple[int, int], object]]


def normalise_formula(formula: str) -> str:
    return UNKNOWN_FUNCTION_PREFIX.sub("_xlfn.", formula)


def _normalise_book(book: openpyxl.Workbook) -> None:
    for sheet in book.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("=") and "_xl" in cell.value:
                    cell.value = normalise_formula(cell.value)


def recalculate(xlsx: Path, overrides: dict[str, dict[str, object]] | None = None) -> Values:
    """Values computed by LibreOffice after applying {sheet: {coord: value}} overrides."""
    book = openpyxl.load_workbook(xlsx, data_only=False)
    _normalise_book(book)
    for sheet_name, changes in (overrides or {}).items():
        for coord, value in changes.items():
            book[sheet_name][coord] = value
    with tempfile.TemporaryDirectory() as tmp:
        stripped = Path(tmp) / "in" / "book.xlsx"
        stripped.parent.mkdir()
        book.save(stripped)
        result = subprocess.run(
            [find_soffice(), "--headless", profile_argument(Path(tmp) / "profile"),
             "--convert-to", "xlsx", "--outdir", str(Path(tmp) / "out"), str(stripped)],
            capture_output=True, text=True, timeout=CONVERT_TIMEOUT_S, check=False,
        )
        computed = Path(tmp) / "out" / "book.xlsx"
        if result.returncode != 0 or not computed.exists():
            raise RuntimeError(f"LibreOffice recalculation failed: {result.stderr.strip() or result.stdout.strip()}")
        return cached_values(computed)


def agrees(excel: object, libre: object) -> bool:
    if isinstance(excel, bool) or isinstance(libre, bool):
        return excel == libre
    if isinstance(excel, (int, float)) and isinstance(libre, (int, float)):
        return math.isclose(excel, libre, rel_tol=ORACLE_REL_TOL, abs_tol=1e-9)
    return excel == libre or (excel in ("", None) and libre in ("", None))


def validate(source: Path) -> str:
    xlsx = to_xlsx(source)
    libre = recalculate(xlsx)
    formulas = [(s.name, c) for s in load_sheets(xlsx, source) for c in s.cells if c.formula]
    bad = [(name, c) for name, c in formulas if not agrees(c.value, libre.get(name, {}).get((c.row, c.col)))]
    shown = "; ".join(
        f"{name}!{c.coord} excel={c.value!r} libre={libre.get(name, {}).get((c.row, c.col))!r}" for name, c in bad[:MAX_SHOWN]
    )
    return f"{workbook_slug(source)}: {len(bad)}/{len(formulas)} formula cells differ" + (f" — {shown}" if bad else "")


def main(only: frozenset[str] = frozenset()) -> int:
    """Validate every workbook, or only the slugs given on the command line."""
    for source in workbook_sources():
        if not only or workbook_slug(source) in only:
            print(validate(source), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(frozenset(sys.argv[1:])))
