"""CLI: python -m extract.run  — dump every workbook to cell maps, CSV data, media and a report."""
import csv
import math
import sys
import zipfile
from pathlib import Path

from .cellmap import render_sheet
from .cells import Sheet, cached_values, load_sheets
from .config import (
    CELLMAP_DIR,
    DATA_DIR,
    MEDIA_DIR,
    REPORT_PATH,
    VALUE_REL_TOL,
    slugify,
    workbook_slug,
    workbook_sources,
)
from .convert import to_xlsx
from .fingerprint import Fingerprint, cell_diff_count, duplicate_groups, fingerprint


def write_csv(sheet: Sheet, target: Path) -> None:
    grid = {(c.row, c.col): c.value for c in sheet.cells}
    if not grid:
        return
    max_row, max_col = max(r for r, _ in grid), max(c for _, c in grid)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(
            [grid.get((r, c), "") for c in range(1, max_col + 1)] for r in range(1, max_row + 1)
        )


def extract_media(xlsx: Path, target_dir: Path) -> int:
    with zipfile.ZipFile(xlsx) as archive:
        media = [n for n in archive.namelist() if n.startswith("xl/media/")]
        for name in media:
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / Path(name).name).write_bytes(archive.read(name))
    return len(media)


def recalc_mismatches(converted: Path, sheets: tuple[Sheet, ...]) -> int:
    """Formula cells where LibreOffice's value differs from Excel's cached value."""
    libre = cached_values(converted)
    return sum(
        1
        for sheet in sheets
        for c in sheet.cells
        if c.formula and not _same(c.value, libre.get(sheet.name, {}).get((c.row, c.col)))
    )


def _same(a: object, b: object) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=VALUE_REL_TOL, abs_tol=1e-12)
    return a == b or (a in ("", None) and b in ("", None))


def process(source: Path, write: bool = True) -> tuple[str, tuple[Sheet, ...], str]:
    """Load one workbook; with write=False only the sheets are returned (for the duplicate report)."""
    slug = workbook_slug(source)
    xlsx = to_xlsx(source)
    sheets = load_sheets(xlsx, source)
    if not write:
        return slug, sheets, f"- `{slug}` ← {source.name}: unchanged (not re-extracted)"
    for sheet in sheets:
        if sheet.cells:
            name = slugify(sheet.name)
            (CELLMAP_DIR / slug).mkdir(parents=True, exist_ok=True)
            (CELLMAP_DIR / slug / f"{name}.txt").write_text(render_sheet(sheet), encoding="utf-8")
            write_csv(sheet, DATA_DIR / slug / f"{name}.csv")
    media = extract_media(xlsx, MEDIA_DIR / slug)
    oracle = f"{recalc_mismatches(xlsx, sheets)} LibreOffice≠Excel" if xlsx != source else "native xlsx"
    return slug, sheets, f"- `{slug}` ← {source.name}: {media} images, {oracle}"


def report(books: dict[str, tuple[Sheet, ...]], notes: list[str]) -> str:
    prints = tuple(fingerprint(slug, s) for slug, sheets in books.items() for s in sheets)
    by_key = {(slug, s.name): s for slug, sheets in books.items() for s in sheets}
    lines = ["# Extraction report", "", "## Workbooks", *notes, "", "## Sheets", "",
             "| workbook | sheet | cells | formulas | full | logic |", "|---|---|---|---|---|---|",
             *(f"| {p.workbook} | {p.sheet} | {p.cells} | {p.formulas} | {p.full} | {p.logic} |" for p in prints)]
    for title, key in (("Identical sheets (same data + logic)", "full"), ("Same logic, different inputs", "logic")):
        lines += ["", f"## {title}", *(_group_line(g, by_key) for g in duplicate_groups(prints, key))]
    return "\n".join(lines) + "\n"


def _group_line(group: tuple[Fingerprint, ...], by_key: dict) -> str:
    first = by_key[(group[0].workbook, group[0].sheet)]
    members = ", ".join(
        f"{p.workbook}/{p.sheet} (Δ{cell_diff_count(first, by_key[(p.workbook, p.sheet)])})" for p in group
    )
    return f"- {members}"


def main(only: frozenset[str] = frozenset()) -> int:
    """Extract every workbook, or re-extract only the given slugs (the rest is loaded for the report)."""
    sources = workbook_sources()
    if not sources:
        print("no workbooks found", file=sys.stderr)
        return 1
    books, notes = {}, []
    for source in sources:
        slug, sheets, note = process(source, write=not only or workbook_slug(source) in only)
        books, notes = {**books, slug: sheets}, [*notes, note]
        print(note)
    REPORT_PATH.write_text(report(books, notes), encoding="utf-8")
    print(f"report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main(frozenset(sys.argv[1:])))
