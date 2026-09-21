import pytest

from strutture.shared.load_table import ReactionRow, validate_unique_nodo_combo


def _row(nodo: int, combo: str) -> ReactionRow:
    return ReactionRow(nodo=nodo, combo=combo, fx_kN=0, fy_kN=0, fz_kN=0, mx_kNm=0, my_kNm=0, mz_kNm=0)


def test_unique_pairs_pass():
    validate_unique_nodo_combo((_row(1, "c1"), _row(1, "c2"), _row(2, "c1")))


def test_duplicate_nodo_combo_raises_naming_1_based_rows():
    rows = (_row(1, "c1"), _row(2, "c1"), _row(1, "c1"))
    with pytest.raises(ValueError, match=r"riga 1 e riga 3"):
        validate_unique_nodo_combo(rows)


def test_o_n_on_20000_rows_with_no_duplicates():
    import time

    rows = tuple(_row(i, "c") for i in range(1, 20_001))  # same combo, distinct nodo -> no duplicate
    start = time.perf_counter()
    validate_unique_nodo_combo(rows)
    assert time.perf_counter() - start < 1.0
