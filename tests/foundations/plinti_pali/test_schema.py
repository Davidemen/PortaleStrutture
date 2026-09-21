import pytest

from strutture.foundations.plinti_pali.schema import grid_counts, numero_pali


@pytest.mark.unit
@pytest.mark.parametrize(("schema", "counts", "n"), [
    ("2x2", (2, 2), 4), ("2x1", (2, 1), 2), ("1x2", (1, 2), 2), ("1x1", (1, 1), 1),
])
def test_grid_counts_e_numero_pali(schema, counts, n) -> None:
    assert grid_counts(schema) == counts
    assert numero_pali(schema) == n
