"""Cross-row validation for the `reazioni` table (§2: unique (nodo, combo)).

Call from the consuming tool's `model_validator(mode="after")`; raise `ValueError` so pydantic
attaches it at the table field (the message names the 1-based rows, per the contract's Italian
error convention)."""
from .models import ReactionRow


def validate_unique_nodo_combo(rows: tuple[ReactionRow, ...]) -> None:
    """Raise `ValueError` on the first (nodo, combo) pair that repeats, naming both 1-based rows.

    O(n): a private, function-local index (never exposed or mutated by the caller) is the only way
    to detect a repeat in one pass over up to 20 000 rows."""
    first_seen_at: dict[tuple[int, str], int] = {}
    for index, row in enumerate(rows):
        key = (row.nodo, row.combo)
        first_index = first_seen_at.get(key)
        if first_index is not None:
            raise ValueError(
                f"riga {first_index + 1} e riga {index + 1}: combinazione '{row.combo}' duplicata per il nodo {row.nodo}"
            )
        first_seen_at[key] = index
