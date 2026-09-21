"""Render a sheet as a compact, row-grouped text map for LLM consumption.

Runs of fill-down formula rows and long constant tables are collapsed, since
they carry no extra logic; full values stay available in the CSV export.
"""
from itertools import groupby

from openpyxl.formula.tokenizer import TokenizerError
from openpyxl.formula.translate import Translator
from openpyxl.utils import get_column_letter

from .cells import Cell, Sheet
from .config import CONST_RUN_MIN, FORMULA_RUN_MIN, MAX_TEXT_LEN, RUN_HEAD_ROWS

Row = tuple[Cell, ...]
MAX_EXACT_INT = 1e15  # whole numbers below this print exactly (e.g. ISTAT codes)


def format_value(value: object) -> str:
    if isinstance(value, bool) or value is None:
        return str(value)
    if isinstance(value, (int, float)):
        is_whole = float(value).is_integer() and abs(value) < MAX_EXACT_INT
        return str(int(value)) if is_whole else f"{value:.6g}"
    text = str(value).replace("\n", " ").strip()
    clipped = text if len(text) <= MAX_TEXT_LEN else f"{text[:MAX_TEXT_LEN]}…"
    return f'"{clipped}"'


def render_cell(cell: Cell) -> str:
    name = f"{get_column_letter(cell.col)}{'*' if cell.unlocked else ''}"
    if cell.formula:
        return f"{name}={{{cell.formula} → {format_value(cell.value)}}}"
    return f"{name}={format_value(cell.value)}"


def render_row(row: Row) -> str:
    return f"{row[0].row}: " + " ".join(render_cell(c) for c in row)


def _shifted(formula: str, origin: str, dest: str) -> str | None:
    try:
        return Translator(formula, origin=origin).translate_formula(dest)
    except (TokenizerError, ValueError):  # unparseable formula: treat as not a fill-down
        return None


def continues_pattern(prev: Row, cur: Row) -> bool:
    """True when cur is prev filled down one row (same columns, same relative formulas)."""
    if cur[0].row != prev[0].row + 1 or [c.col for c in prev] != [c.col for c in cur]:
        return False
    return all(
        (p.formula is None and c.formula is None)
        or (p.formula and c.formula and _shifted(p.formula, p.coord, c.coord) == c.formula)
        for p, c in zip(prev, cur)
    )


def split_runs(rows: tuple[Row, ...]) -> tuple[tuple[Row, ...], ...]:
    runs: list[tuple[Row, ...]] = []
    for row in rows:
        if runs and continues_pattern(runs[-1][-1], row):
            runs = [*runs[:-1], (*runs[-1], row)]
        else:
            runs = [*runs, (row,)]
    return tuple(runs)


def render_run(run: tuple[Row, ...]) -> tuple[str, ...]:
    has_formula = any(c.formula for c in run[0])
    threshold = FORMULA_RUN_MIN if has_formula else CONST_RUN_MIN
    if len(run) < threshold:
        return tuple(render_row(r) for r in run)
    hidden = run[RUN_HEAD_ROWS:-1]
    kind = "fill-down of the formulas above" if has_formula else "constant table rows"
    note = f"  … rows {hidden[0][0].row}-{hidden[-1][0].row}: {len(hidden)} more {kind} (values in CSV)"
    return (*(render_row(r) for r in run[:RUN_HEAD_ROWS]), note, render_row(run[-1]))


def render_sheet(sheet: Sheet) -> str:
    ordered = sorted(sheet.cells, key=lambda c: (c.row, c.col))
    rows = tuple(tuple(group) for _, group in groupby(ordered, key=lambda c: c.row))
    formulas = sum(1 for c in sheet.cells if c.formula)
    header = (
        (f"# sheet {sheet.name!r}: {len(sheet.cells)} cells, {formulas} formulas, "
         f"protected={sheet.protected}; '*' = unlocked cell (likely input)"),
        *(f"# validation {v}" for v in sheet.validations),
    )
    body = tuple(line for run in split_runs(rows) for line in render_run(run))
    return "\n".join((*header, *body)) + "\n"
