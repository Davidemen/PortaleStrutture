"""Zero-token completeness critic for tool specs.

Walks the formula precedents of each declared output and reports:
- unaccounted leaves: constants feeding an output that the spec did not declare as inputs
- unused inputs: declared inputs no output depends on
- candidate outputs: formula cells nothing else references and the spec did not list

Usage: python -m extract.coverage build/specs.json
"""
import json
import re
import sys
from pathlib import Path

from openpyxl.formula.tokenizer import Token, Tokenizer
from openpyxl.utils import range_boundaries

from .cells import Cell, Sheet, load_sheets
from .config import slugify, workbook_slug, workbook_sources
from .convert import to_xlsx

MAX_EXPANDED_RANGE = 60  # larger ranges are lookup tables, not scalar precedents
REF_PATTERN = re.compile(r"^(?:'?([^'!]+)'?!)?(\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?)$")
ADDRESS_PATTERN = re.compile(r"(?:'([^'!]+)'!|([\w.]+)!)?(\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?)(?![\w(])")
ANNOTATION_PATTERN = re.compile(r"\([^)]*\)")  # analysts annotate addresses, e.g. "Z31 (d)"
Key = tuple[str, int, int]  # sheet slug, row, col


def references(formula: str, own_sheet: str) -> tuple[Key, ...]:
    """Cells a formula reads directly (small ranges expanded, table-sized ranges skipped)."""
    tokenizer = Tokenizer(formula.strip("{}"))
    keys: list[Key] = []
    for token in tokenizer.items:
        match = REF_PATTERN.match(token.value) if token.type == Token.OPERAND and token.subtype == Token.RANGE else None
        if not match:
            continue
        sheet = slugify(match.group(1)) if match.group(1) else own_sheet
        min_col, min_row, max_col, max_row = range_boundaries(match.group(2).replace("$", ""))
        if (max_col - min_col + 1) * (max_row - min_row + 1) <= MAX_EXPANDED_RANGE:
            keys.extend((sheet, r, c) for r in range(min_row, max_row + 1) for c in range(min_col, max_col + 1))
    return tuple(keys)


def index_cells(sheets: tuple[Sheet, ...]) -> dict[Key, Cell]:
    return {(slugify(s.name), c.row, c.col): c for s in sheets for c in s.cells}


def closure(start: tuple[Key, ...], cells: dict[Key, Cell]) -> frozenset[Key]:
    seen: set[Key] = set()
    frontier = [k for k in start if k in cells]
    while frontier:
        key = frontier.pop()
        if key in seen:
            continue
        seen.add(key)
        if cells[key].formula:
            frontier.extend(k for k in references(cells[key].formula, key[0]) if k in cells)
    return frozenset(seen)


def to_keys(sheet: str, address: str) -> tuple[Key, ...]:
    """Expand 'H6', 'D13:E16', 'Tabelle!M1', 'J58/J77' or 'Z31 (d)'; a sheet prefix overrides the tool's sheet."""
    found = ADDRESS_PATTERN.findall(ANNOTATION_PATTERN.sub("", address))
    if not found:
        raise ValueError(f"unparseable cell address in spec: {address!r}")
    keys: list[Key] = []
    for quoted, bare, cell_range in found:
        target = slugify(quoted or bare) if (quoted or bare) else sheet
        min_col, min_row, max_col, max_row = range_boundaries(cell_range.replace("$", ""))
        keys.extend((target, r, c) for r in range(min_row, max_row + 1) for c in range(min_col, max_col + 1))
    return tuple(keys)


def table_cells(sheet: str, ranges: list[str]) -> frozenset[Key]:
    """Cells inside the spec's declared lookup tables (accounted for as data, not inputs)."""
    keys: set[Key] = set()
    for text in ranges:
        match = REF_PATTERN.match(text.strip())
        if not match:
            continue
        target = slugify(match.group(1)) if match.group(1) else sheet
        min_col, min_row, max_col, max_row = range_boundaries(match.group(2).replace("$", ""))
        keys.update((target, r, c) for r in range(min_row, max_row + 1) for c in range(min_col, max_col + 1))
    return frozenset(keys)


def check_tool(tool: dict, cells: dict[Key, Cell]) -> dict:
    sheet = tool["sheet"].split("/")[-1]
    inputs = frozenset(k for a in tool["inputs"] for k in to_keys(sheet, a)) | table_cells(sheet, tool.get("tables", []))
    declared = frozenset(k for a in tool["inputs"] for k in to_keys(sheet, a))
    outputs = tuple(k for a in tool["outputs"] for k in to_keys(sheet, a))
    reached = closure(outputs, cells)
    numeric_leaves = {k for k in reached if not cells[k].formula and isinstance(cells[k].value, (int, float))}
    referenced = {r for k, c in cells.items() if c.formula for r in references(c.formula, k[0])}
    terminals = {k for k, c in cells.items() if k[0] == sheet and c.formula and k not in referenced and k not in outputs}
    return {
        "tool": tool["name"],
        "missing_cells": sorted(cells_label(k) for k in (*declared, *outputs) if k not in cells),
        "unaccounted_leaves": sorted(cells_label(k, cells) for k in numeric_leaves - inputs),
        "unused_inputs": sorted(cells_label(k) for k in declared - reached),
        "candidate_outputs": sorted(cells_label(k, cells) for k in terminals),
    }


def cells_label(key: Key, cells: dict[Key, Cell] | None = None) -> str:
    cell = cells.get(key) if cells else None
    coord = cell.coord if cell else f"r{key[1]}c{key[2]}"
    return f"{key[0]}!{coord}" + (f"={cell.value!r}" if cell else "")


def main(spec_path: str) -> int:
    specs = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    sources = {workbook_slug(p): p for p in workbook_sources()}
    tools = [t for unit in specs for t in unit["tools"]]
    needed = {t["sheet"].split("/")[0] for t in tools} & sources.keys()
    books = {slug: index_cells(load_sheets(to_xlsx(sources[slug]), sources[slug])) for slug in needed}
    print(json.dumps([_checked(t, books) for t in tools], ensure_ascii=False, indent=1))
    return 0


def _checked(tool: dict, books: dict[str, dict[Key, Cell]]) -> dict:
    slug = tool["sheet"].split("/")[0]
    if slug not in books:
        return {"tool": tool["name"], "error": f"unknown workbook {slug!r}"}
    try:
        return check_tool(tool, books[slug])
    except ValueError as error:
        return {"tool": tool["name"], "error": str(error)}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
