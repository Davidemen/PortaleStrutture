"""Envelope over a `reazioni` table: governing max/min/absmax of a per-row quantity (§1.2, §2).

`value` may return `None` for a row where the quantity is undefined (e.g. zero demand, §1
"senza_domanda"); such rows are skipped rather than treated as 0, so they can never win a `min`
envelope by accident. Ties keep the first row (matches the sheet's `XLOOKUP(..., 0, 1)` — exact
match, search-forward, §7)."""
from collections.abc import Callable

from .grouping import group_by_famiglia
from .models import EnvelopeMode, EnvelopeRow, Famiglia, ReactionRow

ValueFn = Callable[[ReactionRow], float | None]


def governing(rows: tuple[ReactionRow, ...], value: ValueFn, mode: EnvelopeMode) -> EnvelopeRow | None:
    """Single governing row over the whole table (O(n)); `None` if every row is undefined."""
    best_index: int | None = None
    best_value: float | None = None
    for index, row in enumerate(rows):
        candidate = value(row)
        if candidate is None:
            continue
        ranked = abs(candidate) if mode == "absmax" else candidate
        if best_value is None or _beats(ranked, best_value, mode):
            best_index, best_value = index, ranked
    if best_index is None:
        return None
    row = rows[best_index]
    return EnvelopeRow(famiglia=row.famiglia, valore=value(row), combo=row.combo, nodo=row.nodo, indice=best_index)


def envelope(
    rows: tuple[ReactionRow, ...],
    value: ValueFn,
    mode: EnvelopeMode,
    by: str | None = "famiglia",
) -> tuple[EnvelopeRow, ...]:
    """One `EnvelopeRow` per group (`by="famiglia"`, `by=None` for a single global envelope), O(n)."""
    if by is None:
        result = governing(rows, value, mode)
        return () if result is None else (result,)
    if by != "famiglia":
        raise ValueError(f"envelope: unsupported grouping {by!r} (use 'famiglia' or None)")
    groups: tuple[tuple[Famiglia | None, tuple[ReactionRow, ...]], ...] = group_by_famiglia(rows)
    envelope_rows = (governing(group_rows, value, mode) for _, group_rows in groups)
    return tuple(row for row in envelope_rows if row is not None)


def _beats(candidate: float, current_best: float, mode: EnvelopeMode) -> bool:
    if mode == "min":
        return candidate < current_best
    return candidate > current_best  # "max" and "absmax" both rank higher-first
