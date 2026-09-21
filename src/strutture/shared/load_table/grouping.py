"""Grouping helpers over a `reazioni` table, O(n), pure tuples (no dict handed back to the caller)."""
from .models import Famiglia, ReactionRow


def group_by_famiglia(rows: tuple[ReactionRow, ...]) -> tuple[tuple[Famiglia | None, tuple[ReactionRow, ...]], ...]:
    """Rows split by `famiglia`, in first-appearance order (stable, one pass)."""
    return _group_by(rows, key=lambda row: row.famiglia)


def group_by_nodo(rows: tuple[ReactionRow, ...]) -> tuple[tuple[int, tuple[ReactionRow, ...]], ...]:
    """Rows split by `nodo`, in first-appearance order (stable, one pass)."""
    return _group_by(rows, key=lambda row: row.nodo)


def _group_by[K](rows: tuple[ReactionRow, ...], *, key) -> tuple[tuple[K, tuple[ReactionRow, ...]], ...]:
    buckets: dict[K, list[ReactionRow]] = {}
    order: list[K] = []
    for row in rows:
        bucket_key = key(row)
        bucket = buckets.get(bucket_key)
        if bucket is None:
            buckets[bucket_key] = [row]
            order.append(bucket_key)
        else:
            bucket.append(row)
    return tuple((bucket_key, tuple(buckets[bucket_key])) for bucket_key in order)
