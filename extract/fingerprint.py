"""Sheet fingerprints: find sheets duplicated across workbooks (shared data / shared logic)."""
import hashlib
from collections import defaultdict
from dataclasses import dataclass

from .cells import Sheet

HASH_LEN = 10


@dataclass(frozen=True)
class Fingerprint:
    workbook: str
    sheet: str
    cells: int
    formulas: int
    full: str    # formulas + constants
    logic: str   # formulas only: equal => same calculation, different inputs


def _digest(items: list[str]) -> str:
    return hashlib.sha1("\n".join(sorted(items)).encode()).hexdigest()[:HASH_LEN]


def fingerprint(workbook: str, sheet: Sheet) -> Fingerprint:
    formulas = [f"{c.coord}|{c.formula}" for c in sheet.cells if c.formula]
    constants = [f"{c.coord}|{c.value!r}" for c in sheet.cells if not c.formula]
    return Fingerprint(
        workbook=workbook,
        sheet=sheet.name,
        cells=len(sheet.cells),
        formulas=len(formulas),
        full=_digest(formulas + constants),
        logic=_digest(formulas) if formulas else "-",
    )


def duplicate_groups(prints: tuple[Fingerprint, ...], key: str) -> tuple[tuple[Fingerprint, ...], ...]:
    groups: dict[str, tuple[Fingerprint, ...]] = defaultdict(tuple)
    for fp in prints:
        if fp.cells and getattr(fp, key) != "-":
            groups[getattr(fp, key)] = (*groups[getattr(fp, key)], fp)
    return tuple(g for g in groups.values() if len(g) > 1)


def cell_diff_count(a: Sheet, b: Sheet) -> int:
    left = {c.coord: c.formula or c.value for c in a.cells}
    right = {c.coord: c.formula or c.value for c in b.cells}
    return sum(1 for k in left.keys() | right.keys() if left.get(k) != right.get(k))
