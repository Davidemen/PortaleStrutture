"""E2E coverage of the table-input widget (DESIGN_SPEC §4b) against the in-process demo tool.

No real table tool exists until batch 2 lands (per §4b "E2E" note); `demo-tabella` is
registered by the `live_server` fixture (`_demo_tool.py`) for exactly this purpose.
"""
import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool, load_example, submit

pytestmark = pytest.mark.e2e

TABLE = "[data-field='stratigrafia'] table"


def _open_paste_panel(page: Page) -> None:
    # `<summary>` has no accessible "button" role in Chromium's a11y tree, so target it as
    # plain text rather than `get_by_role("button", ...)` (table-input.js's own markup).
    page.get_by_text("Incolla da Excel", exact=True).click()


def test_paste_tsv_with_aliases_and_decimal_comma(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-tabella")
    _open_paste_panel(page)
    tsv = "profondità (m)\tmodulo (mpa)\n0\t15,5\n2,5\t22,0\n"
    page.locator("textarea").fill(tsv)
    # "Sostituisci" is the (default-checked) paste-mode radio, not a button; "Applica" runs it.
    page.get_by_role("button", name="Applica").click()

    rows = page.locator(f"{TABLE} tbody tr")
    expect(rows).to_have_count(2)
    second_row_modulo = rows.nth(1).locator("input, select").nth(1)
    expect(second_row_modulo).to_have_value("22")


def test_add_and_delete_row(page: Page, base_url: str) -> None:
    # `stratigrafia` has `min_length=1`; start from the 2-row example rather than an empty
    # table so the delete step below never has to cross the minItems floor.
    goto_tool(page, base_url, "demo-tabella")
    load_example(page)
    before = page.locator(f"{TABLE} tbody tr").count()
    assert before >= 1, "expected the example to prefill at least one row"
    page.get_by_role("button", name="Aggiungi riga").click()
    expect(page.locator(f"{TABLE} tbody tr")).to_have_count(before + 1)

    # table-input.js's own label is "Elimina" (no "riga" suffix).
    page.locator(f"{TABLE} tbody tr").last.get_by_role("button", name="Elimina").click()
    expect(page.locator(f"{TABLE} tbody tr")).to_have_count(before)


def test_cell_level_server_error(page: Page, base_url: str) -> None:
    # `modulo_mpa` has no client-side range check (only the server's `gt=0` does, on purpose --
    # see validate.js), so an out-of-range cell round-trips to the server's `error_details` and
    # exercises `setCellError` rather than being blocked before submission.
    goto_tool(page, base_url, "demo-tabella")
    load_example(page)
    first_row = page.locator(f"{TABLE} tbody tr").first
    modulo_cell = first_row.locator("input, select").nth(1)
    modulo_cell.fill("-5")
    submit(page)

    expect(modulo_cell).to_have_attribute("aria-invalid", "true")
    summary_text = page.locator("#error-summary").inner_text()
    assert "riga 1" in summary_text or "riga 0" in summary_text, f"row not located in summary: {summary_text!r}"


def test_csv_template_download(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-tabella")
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Scarica modello CSV").click()
    path = download_info.value.path()
    assert path is not None
    header = path.read_bytes().decode("utf-8-sig").splitlines()[0]
    assert "z" in header and "E" in header, f"template header missing column symbols: {header!r}"


def test_collapses_above_preview_rows(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-tabella")
    _open_paste_panel(page)
    rows = "\n".join(f"{i}\t{10 + i}" for i in range(6))
    page.locator("textarea").fill(f"z\tE\n{rows}\n")
    page.get_by_role("button", name="Applica").click()

    # `.f-table` and its parent `.f-field` both carry `data-field="stratigrafia"`; scope to the
    # inner one (id="field-stratigrafia") to avoid an ambiguous match.
    collapsed = page.locator("#field-stratigrafia").inner_text()
    assert "6 righe" in collapsed, f"expected the '6 righe caricate' collapse message, got: {collapsed!r}"
