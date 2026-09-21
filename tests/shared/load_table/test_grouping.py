from strutture.shared.load_table import ReactionRow, group_by_famiglia, group_by_nodo


def _row(nodo: int, combo: str, famiglia: str | None) -> ReactionRow:
    return ReactionRow(nodo=nodo, combo=combo, famiglia=famiglia, fx_kN=0, fy_kN=0, fz_kN=0, mx_kNm=0, my_kNm=0, mz_kNm=0)


ROWS = (
    _row(1, "c1", "SLU_STR"),
    _row(1, "c2", "SLE_QP"),
    _row(2, "c3", "SLU_STR"),
    _row(2, "c4", None),
)


def test_group_by_famiglia_preserves_first_appearance_order():
    groups = group_by_famiglia(ROWS)
    assert [key for key, _ in groups] == ["SLU_STR", "SLE_QP", None]
    assert dict(groups)["SLU_STR"] == (ROWS[0], ROWS[2])


def test_group_by_nodo():
    groups = group_by_nodo(ROWS)
    assert [key for key, _ in groups] == [1, 2]
    assert dict(groups)[1] == (ROWS[0], ROWS[1])
    assert dict(groups)[2] == (ROWS[2], ROWS[3])


def test_grouping_returns_pure_tuples_no_row_dropped():
    groups = group_by_famiglia(ROWS)
    assert sum(len(rows) for _, rows in groups) == len(ROWS)
