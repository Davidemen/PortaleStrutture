"""Unit tests for the pure parts of the extraction pipeline."""
from extract.cellmap import continues_pattern, format_value, render_run, split_runs
from extract.cells import Cell
from extract.config import FORMULA_RUN_MIN, slugify
from extract.coverage import closure, references, table_cells


def row(r, formula_col_b=True):
    formula = f"=A{r}*2" if formula_col_b else None
    return (Cell(r, 1, None, r, False), Cell(r, 2, formula, r * 2, False))


def test_format_value_keeps_whole_numbers_exact():
    assert format_value(13069001.0) == "13069001"
    assert format_value(0.123456789) == "0.123457"
    assert format_value("a\nb") == '"a b"'


def test_fill_down_rows_continue_pattern():
    assert continues_pattern(row(1), row(2))
    assert not continues_pattern(row(1), row(3))  # gap
    broken = (Cell(2, 1, None, 2, False), Cell(2, 2, "=A1*2", 4, False))
    assert not continues_pattern(row(1), broken)  # reference did not shift


def test_long_formula_runs_are_collapsed():
    rows = tuple(row(r) for r in range(1, FORMULA_RUN_MIN + 5))
    runs = split_runs(rows)
    assert len(runs) == 1
    lines = render_run(runs[0])
    assert len(lines) == 4 and "more fill-down" in lines[2]


def test_references_expand_small_ranges_and_skip_tables():
    refs = references("=SUM(A1:A3)+'Other Sheet'!$B$2+VLOOKUP(C1,Tabelle!A1:Z99,2,FALSE)", "main")
    assert ("main", 1, 1) in refs and ("main", 3, 1) in refs
    assert ("other-sheet", 2, 2) in refs
    assert not any(sheet == "tabelle" for sheet, _, _ in refs)


def test_closure_walks_precedents():
    cells = {
        ("s", 1, 1): Cell(1, 1, None, 5, True),
        ("s", 1, 2): Cell(1, 2, "=A1*2", 10, False),
        ("s", 1, 3): Cell(1, 3, "=B1+1", 11, False),
        ("s", 9, 9): Cell(9, 9, None, 0, False),
    }
    assert closure((("s", 1, 3),), cells) == {("s", 1, 1), ("s", 1, 2), ("s", 1, 3)}


def test_table_cells_and_slugify():
    assert ("tabelle", 2, 1) in table_cells("main", ["Tabelle!A1:B2"])
    assert ("main", 1, 1) in table_cells("main", ["$A$1:$A$2"])
    assert slugify("Verifica instabilità (X)") == "verifica-instabilita-x"


def test_modern_functions_saved_by_an_old_excel_are_normalised():
    from extract.oracle import normalise_formula

    assert normalise_formula("=+_xll.XLOOKUP(L16,A:A,B:B,0,1)") == "=+_xlfn.XLOOKUP(L16,A:A,B:B,0,1)"
    assert normalise_formula("=_xludf.XLOOKUP(A1,B:B,C:C)+_xlfn.COT(D1)") == "=_xlfn.XLOOKUP(A1,B:B,C:C)+_xlfn.COT(D1)"
    assert normalise_formula("=SUM(A1:A3)") == "=SUM(A1:A3)"


def test_soffice_candidates_cover_windows_and_mac():
    from extract.config import SOFFICE_CANDIDATES

    joined = " ".join(SOFFICE_CANDIDATES)
    assert "LibreOffice.app" in joined and "Program Files" in joined and "soffice" in SOFFICE_CANDIDATES


def test_profile_argument_is_a_valid_file_uri_on_every_platform(tmp_path):
    from extract.convert import profile_argument

    argument = profile_argument(tmp_path)
    assert argument.startswith("-env:UserInstallation=file:///") and "\\" not in argument
