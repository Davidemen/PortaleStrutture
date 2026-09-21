"""Pile counts per axis for each `shared.pile_group.SchemaPali` value (`Footing check!AM23`
"Case 1".."Case 4"): needed by the legacy per-pile-share formula and by the strut-and-tie geometry,
which both branch on "how many piles per row/column", not on the coordinates themselves."""
from strutture.shared.pile_group import SchemaPali

GRID_COUNTS: dict[SchemaPali, tuple[int, int]] = {
    "2x2": (2, 2),
    "2x1": (2, 1),
    "1x2": (1, 2),
    "1x1": (1, 1),
}


def grid_counts(schema_pali: SchemaPali) -> tuple[int, int]:
    """(count_x, count_y) piles along each axis for the given `schema_pali`."""
    return GRID_COUNTS[schema_pali]


def numero_pali(schema_pali: SchemaPali) -> int:
    count_x, count_y = grid_counts(schema_pali)
    return count_x * count_y
