"""Unit tests for the embedded Eisenmann coefficient table (spec 'pav-eisenman', 160 rows from
`build/data/pavimento-industriale/eisenman.csv`, dead data on the main sheet -- see the module
docstring for why this package embeds it without registering a second `Tool`)."""
from itertools import pairwise

import pytest

from strutture.foundations.pavimento_industriale.eisenmann import EISENMANN_TABLE, eisenmann_coefficiente
from strutture.shared.tables import KeyNotFound


@pytest.mark.unit
def test_table_has_160_rows_ascending() -> None:
    assert len(EISENMANN_TABLE) == 160
    xs = [x for x, _ in EISENMANN_TABLE]
    assert xs == sorted(xs)


@pytest.mark.unit
def test_exact_row_hits_return_the_cached_value() -> None:
    assert eisenmann_coefficiente(0.2) == pytest.approx(0.1921)
    assert eisenmann_coefficiente(3.38) == pytest.approx(0.0008)


@pytest.mark.unit
def test_interpolates_between_bracketing_rows() -> None:
    coeff = eisenmann_coefficiente(0.21)  # between (0.2, 0.1921) and (0.22, 0.1884)
    assert 0.1884 < coeff < 0.1921


@pytest.mark.unit
def test_monotonically_decreasing_curve() -> None:
    values = [y for _, y in EISENMANN_TABLE]
    assert all(a >= b for a, b in pairwise(values))


@pytest.mark.unit
def test_out_of_range_raises() -> None:
    with pytest.raises(KeyNotFound):
        eisenmann_coefficiente(0.1)
    with pytest.raises(KeyNotFound):
        eisenmann_coefficiente(4.0)
