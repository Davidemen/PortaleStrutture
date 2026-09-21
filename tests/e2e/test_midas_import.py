"""E2E coverage of the MIDAS import dialog (MIDAS.md §5/§6): the real backend routes and relay
are not available yet, so every /api/midas/* call is stubbed at OUR API boundary with
contract-shaped JSON (`_midas_fixtures.py`) via `page.route`. Runs against two in-process demo
tools (`_demo_tool.py`): `demo-tabella-midas` (a `reazioni` table carrying the
`table.source = "midas-reactions"` hint, using the real `ReactionRow` model) and `demo-tabella`
(a table with no `source` hint, the negative control).
"""
import pytest
from playwright.sync_api import Page, expect

from ._actions import CALCOLA, goto_tool
from ._midas_fixtures import install_happy_path, install_verify_error

pytestmark = pytest.mark.e2e

IMPORT_BUTTON = "Importa da MIDAS"
TABLE = "[data-field='reazioni'] table"


def _open_dialog(page: Page) -> None:
    page.get_by_role("button", name=IMPORT_BUTTON).click()
    expect(page.locator(".midas-dialog")).to_be_visible()


def test_import_button_only_on_tables_with_the_hint(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-tabella-midas")
    expect(page.get_by_role("button", name=IMPORT_BUTTON)).to_be_visible()

    goto_tool(page, base_url, "demo-tabella")
    expect(page.get_by_role("button", name=IMPORT_BUTTON)).to_have_count(0)
    # The table itself must still render normally, just without the source-specific button.
    expect(page.get_by_text("Incolla da Excel", exact=True)).to_be_visible()


def test_happy_path_fills_table_and_tool_runs(page: Page, base_url: str) -> None:
    install_happy_path(page)
    goto_tool(page, base_url, "demo-tabella-midas")
    _open_dialog(page)

    # Step 1 -- Connessione: no server key (fixture), so the key field is offered; verify.
    expect(page.locator("#midas-key")).to_be_visible()
    page.get_by_role("button", name="Verifica connessione").click()
    expect(page.locator(".midas-summary")).to_contain_text("Gen NX")
    page.get_by_role("button", name="Avanti").click()

    # Step 2 -- Combinazioni: "solo attive" (default) hides the INACTIVE combination.
    expect(page.get_by_text("OLD(CB)")).to_have_count(0)
    page.locator(".midas-combo-row", has_text="SLU1(CB)").locator("input[type=checkbox]").check()
    page.get_by_role("button", name="Avanti").click()

    # Step 3 -- Appoggi: default "tutti i nodi vincolati", showing the /supports count.
    expect(page.get_by_text("Tutti i nodi vincolati (3)")).to_be_visible()
    page.get_by_role("button", name="Avanti").click()

    # Step 4 -- Importa (mode defaults to "sostituisci").
    page.get_by_role("button", name="Importa", exact=True).click()
    expect(page.locator(".midas-dialog")).to_have_count(0)

    rows = page.locator(f"{TABLE} tbody tr")
    expect(rows).to_have_count(2)
    first = rows.nth(0)
    assert first.locator("[data-col='nodo']").input_value() == "1"
    assert first.locator("[data-col='combo']").input_value() == "SLU1"
    assert first.locator("[data-col='famiglia']").input_value() == "SLU_STR"
    assert first.locator("[data-col='fx_kN']").input_value() == "1"
    assert first.locator("[data-col='fz_kN']").input_value() == "100"

    expect(page.locator("#field-reazioni-error")).to_contain_text("2 righe importate da MIDAS")

    page.get_by_role("button", name=CALCOLA).click()
    value_cell = page.locator("#results-root .r-row[data-field='numero_righe'] .r-cell-value")
    expect(value_cell).to_have_text("2")


def test_key_never_leaves_sessionstorage(page: Page, base_url: str) -> None:
    install_happy_path(page)
    goto_tool(page, base_url, "demo-tabella-midas")
    _open_dialog(page)

    secret = "TEST-SECRET-KEY-99887766"
    key_input = page.locator("#midas-key")
    expect(key_input).to_be_visible()
    key_input.fill(secret)

    assert page.evaluate("window.sessionStorage.getItem('midas.key')") == secret
    assert secret not in page.evaluate("JSON.stringify(window.localStorage)")
    assert secret not in page.url
    key_value_attribute = page.evaluate("document.querySelector('#midas-key').getAttribute('value')")
    assert key_value_attribute is None or secret not in key_value_attribute
    assert secret not in page.evaluate("document.querySelector('.midas-dialog').outerHTML")


def test_verify_error_rendered_in_alert_region(page: Page, base_url: str) -> None:
    install_verify_error(page)
    goto_tool(page, base_url, "demo-tabella-midas")
    _open_dialog(page)

    page.get_by_role("button", name="Verifica connessione").click()

    alert = page.locator(".midas-alert")
    expect(alert).to_have_attribute("role", "alert")
    expect(alert).to_contain_text("Chiave non valida o scaduta")
    expect(page.get_by_role("button", name="Avanti")).to_be_disabled()


def test_keyboard_only_open_and_escape_closes(page: Page, base_url: str) -> None:
    install_happy_path(page)
    goto_tool(page, base_url, "demo-tabella-midas")

    trigger = page.get_by_role("button", name=IMPORT_BUTTON)
    trigger.focus()
    page.keyboard.press("Enter")

    dialog = page.locator(".midas-dialog")
    expect(dialog).to_be_visible()
    assert page.evaluate("document.activeElement.closest('.midas-dialog') !== null"), "focus must move into the dialog on open"

    page.keyboard.press("Escape")
    expect(dialog).to_have_count(0)
    expect(trigger).to_be_focused()


def test_mobile_dialog_no_horizontal_overflow(mobile_page: tuple[Page, object], base_url: str) -> None:
    page, _ = mobile_page
    install_happy_path(page)
    goto_tool(page, base_url, "demo-tabella-midas")
    _open_dialog(page)

    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 0, f"page scrolls horizontally at 390px with the MIDAS dialog open: {overflow}px"

    heights = page.locator(".midas-actions button, .midas-dialog .midas-btn, .midas-dialog .midas-btn-primary").evaluate_all(
        "nodes => nodes.filter(n => n.getBoundingClientRect().height > 0).map(n => n.getBoundingClientRect().height)"
    )
    undersized = [h for h in heights if h < 44]
    assert not undersized, f"MIDAS dialog controls below the 44px tap target: {undersized}"
