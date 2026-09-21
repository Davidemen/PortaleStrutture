from strutture.shared.load_table import ReactionRow, envelope, governing


def _row(nodo: int, combo: str, famiglia: str | None, fz_kN: float) -> ReactionRow:
    return ReactionRow(nodo=nodo, combo=combo, famiglia=famiglia, fx_kN=0, fy_kN=0, fz_kN=fz_kN, mx_kNm=0, my_kNm=0, mz_kNm=0)


ROWS = (
    _row(1, "c1", "SLU_STR", 100.0),
    _row(1, "c2", "SLU_STR", 250.0),
    _row(2, "c3", "SLE_QP", -30.0),
    _row(2, "c4", "SLE_QP", 10.0),
)


def _fz(row: ReactionRow) -> float:
    return row.fz_kN


def test_governing_max():
    result = governing(ROWS, _fz, "max")
    assert result is not None
    assert (result.valore, result.combo, result.nodo, result.indice) == (250.0, "c2", 1, 1)


def test_governing_min():
    result = governing(ROWS, _fz, "min")
    assert result is not None
    assert (result.valore, result.combo) == (-30.0, "c3")


def test_governing_absmax_reports_signed_value():
    result = governing(ROWS, _fz, "absmax")
    assert result is not None
    # |250| > |-30|, but check the |-30| case wins when it is the largest magnitude
    smaller = ROWS[:3]  # 100, 250, -30 -> absmax is still 250
    assert governing(smaller, _fz, "absmax").valore == 250.0
    only_negative_wins = (ROWS[2], ROWS[3])  # -30, 10 -> absmax is -30 (kept signed)
    assert governing(only_negative_wins, _fz, "absmax").valore == -30.0


def test_governing_ties_keep_first_row():
    tied = (_row(1, "first", "SLU_STR", 50.0), _row(1, "second", "SLU_STR", 50.0))
    result = governing(tied, _fz, "max")
    assert result.combo == "first"


def test_governing_skips_undefined_rows():
    def sometimes_none(row: ReactionRow) -> float | None:
        return None if row.combo == "c2" else row.fz_kN

    result = governing(ROWS, sometimes_none, "max")
    assert result.combo == "c1"  # c2 (the true max) is undefined and must be skipped


def test_governing_all_undefined_returns_none():
    assert governing(ROWS, lambda row: None, "max") is None


def test_envelope_by_famiglia_returns_one_row_per_group():
    result = envelope(ROWS, _fz, "max", by="famiglia")
    values = {row.famiglia: (row.valore, row.combo) for row in result}
    assert values == {"SLU_STR": (250.0, "c2"), "SLE_QP": (10.0, "c4")}


def test_envelope_global_when_by_none():
    result = envelope(ROWS, _fz, "max", by=None)
    assert len(result) == 1
    assert result[0].valore == 250.0
    assert result[0].famiglia == "SLU_STR"


def test_envelope_rejects_unsupported_grouping():
    import pytest

    with pytest.raises(ValueError, match="unsupported grouping"):
        envelope(ROWS, _fz, "max", by="nodo")


def test_envelope_o_n_on_large_table():
    import time

    rows = tuple(_row(i, f"c{i}", "SLU_STR", float(i)) for i in range(1, 20_001))
    start = time.perf_counter()
    result = envelope(rows, _fz, "max", by=None)
    elapsed = time.perf_counter() - start
    assert result[0].valore == 20_000.0
    assert elapsed < 1.0
