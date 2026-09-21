"""WORKBENCH_SPEC §11 -- the report personalisation overlay. `demo-relazione`
(tests/e2e/_demo_tool.py) gives a deterministic checks list (5 checks, 1 failing), one nested
result group ("Dettagli di calcolo") and a 5-row table, independent of any real tool's example
data size. `muro-sostegno` (five real result groups) covers the orientation/@page check, which
needs a genuinely printable tool with a norm/title worth asserting on."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import field_id, goto_tool, load_example
from ._collectors import PageCollectors, csp_violations

pytestmark = pytest.mark.e2e

REFUSAL_TEXT = "I risultati non corrispondono ai dati correnti — correggi i dati o ricalcola prima di stampare"
OVERLAY = "#relazione-overlay"


def _stub_print(page: Page) -> None:
    page.evaluate("() => { window.__printed = 0; window.print = () => { window.__printed++; }; }")


def _open_via_button(page: Page) -> None:
    page.get_by_role("button", name="Stampa relazione").click()


def _open_via_menu(page: Page) -> None:
    page.locator(".f-menu-btn").click()
    page.locator(".f-menu-item", has_text="Stampa relazione").click()


def _open_via_ctrl_p(page: Page) -> None:
    page.keyboard.press("Control+p")


def _load_demo(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")


@pytest.mark.parametrize("opener", [_open_via_button, _open_via_menu, _open_via_ctrl_p])
def test_entry_point_opens_overlay_without_printing(page: Page, base_url: str, opener) -> None:
    _load_demo(page, base_url)
    _stub_print(page)
    opener(page)
    expect(page.locator(OVERLAY)).to_be_visible()
    expect(page.locator(OVERLAY)).to_have_attribute("aria-modal", "true")
    assert page.get_attribute(OVERLAY, "role") == "dialog"
    assert page.evaluate("window.__printed") == 0, "opening the overlay must never call window.print()"


def test_ctrl_p_prints_when_overlay_already_open(page: Page, base_url: str) -> None:
    _load_demo(page, base_url)
    _stub_print(page)
    page.keyboard.press("Control+p")
    expect(page.locator(OVERLAY)).to_be_visible()
    page.keyboard.press("Control+p")  # second press while open: prints, does not reopen
    page.wait_for_timeout(150)
    assert page.evaluate("window.__printed") == 1
    expect(page.locator(OVERLAY)).to_be_visible(), "the overlay stays open after printing (Annulla/Esc closes it)"


def test_stale_results_refuse_to_open(page: Page, base_url: str) -> None:
    _load_demo(page, base_url)
    _stub_print(page)
    page.fill(field_id("fattore"), "-1")
    page.locator(field_id("fattore")).blur()
    expect(page.locator(f"{field_id('fattore')}-error")).to_be_visible()
    _open_via_button(page)
    expect(page.locator("#run-error")).to_have_text(REFUSAL_TEXT)
    assert page.locator(OVERLAY).count() == 0
    assert page.evaluate("window.__printed") == 0


def test_defaults_match_the_beforeprint_fallback_byte_for_byte(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §11 acceptance: "defaults produce the §10 document byte-for-byte". Dispatches
    a bare `beforeprint` event to exercise js/relazione-print.js's OWN fallback (a real browser
    menu print that never opened the overlay) with nothing stubbed in its way, then compares it
    against the overlay's untouched (Completa) "Stampa / Salva PDF" output."""
    _load_demo(page, base_url)
    page.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
    page.locator("#relazione-print-root .print-cartiglio").wait_for(state="attached")
    fallback_html = page.locator("#relazione-print-root").inner_html()
    page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")

    _stub_print(page)
    _open_via_button(page)
    expect(page.locator(OVERLAY)).to_be_visible()
    page.get_by_role("button", name="Stampa / Salva PDF").click()
    page.locator("#relazione-print-root .print-cartiglio").wait_for(state="attached")
    overlay_html = page.locator("#relazione-print-root").inner_html()

    assert overlay_html == fallback_html, "the overlay's default output must be byte-for-byte the §10 complete document"


def test_sintetica_removes_documented_sections_and_lists_them(page: Page, base_url: str) -> None:
    _load_demo(page, base_url)
    _stub_print(page)
    _open_via_button(page)
    expect(page.locator(OVERLAY)).to_be_visible()

    page.locator("#rel-preset-sintetica").check()
    omessi = page.locator(".rel-page-content .print-omessi")
    expect(omessi).to_be_visible()
    text = omessi.inner_text()
    for expected in ["Passaggi di calcolo", "Tabelle", "Grafici", "Avvisi", "1 gruppi di risultati"]:
        assert expected in text, f"expected {expected!r} in omessi line {text!r}"
    # Sintetica keeps cartiglio/schizzo/dati/sintesi/verifiche -- none of those show up as omitted.
    for kept in ["Sintesi", "Dati di ingresso"]:
        assert kept not in text

    page.get_by_role("button", name="Stampa / Salva PDF").click()
    page.wait_for_timeout(200)
    root = page.locator("#relazione-print-root")
    assert root.locator(".r-group-title", has_text="Passaggi di calcolo").count() == 0
    assert root.locator(".r-group-title", has_text="Dettagli di calcolo").count() == 0
    expect(root.locator(".print-omessi")).to_contain_text("Passaggi di calcolo")


def test_unticking_one_result_group_removes_it_and_adds_to_omessi(page: Page, base_url: str) -> None:
    _load_demo(page, base_url)
    _stub_print(page)
    _open_via_button(page)
    expect(page.locator(OVERLAY)).to_be_visible()

    group_checkbox = page.locator('[id^="rel-gruppo-"]').first
    expect(group_checkbox).to_be_checked()
    group_checkbox.uncheck()

    expect(page.locator("#rel-preset-personalizzata")).to_be_checked()
    omessi = page.locator(".rel-page-content .print-omessi")
    expect(omessi).to_contain_text("1 gruppi di risultati")
    assert page.locator(".rel-page-content .r-group-title", has_text="Dettagli di calcolo").count() == 0

    page.get_by_role("button", name="Stampa / Salva PDF").click()
    page.wait_for_timeout(200)
    root = page.locator("#relazione-print-root")
    assert root.locator(".r-group-title", has_text="Dettagli di calcolo").count() == 0
    expect(root.locator(".print-omessi")).to_contain_text("1 gruppi di risultati")


def test_verifiche_solo_non_soddisfatte(page: Page, base_url: str) -> None:
    _load_demo(page, base_url)
    _stub_print(page)
    _open_via_button(page)
    expect(page.locator(OVERLAY)).to_be_visible()

    page.locator("#rel-verifiche-non-soddisfatte").check()
    expect(page.locator("#rel-preset-personalizzata")).to_be_checked()
    page.wait_for_timeout(500)  # debounced preview update
    assert page.locator(".rel-page-content .r-check").count() == 1, "only the failing check should preview"

    page.get_by_role("button", name="Stampa / Salva PDF").click()
    page.wait_for_timeout(200)
    checks = page.locator("#relazione-print-root .r-check")
    assert checks.count() == 1
    assert checks.first.get_attribute("data-passed") == "false"


def test_table_row_policy_prime_n(page: Page, base_url: str) -> None:
    _load_demo(page, base_url)
    _stub_print(page)
    _open_via_button(page)
    expect(page.locator(OVERLAY)).to_be_visible()

    page.locator("#rel-righe-prime").check()
    page.fill("#rel-righe-n", "2")
    page.wait_for_timeout(500)

    page.get_by_role("button", name="Stampa / Salva PDF").click()
    page.wait_for_timeout(200)
    rows = page.locator("#relazione-print-root .r-table-print tbody tr")
    assert rows.count() == 2, f"expected exactly 2 rows with 'Prime N'=2, found {rows.count()}"
    expect(page.locator("#relazione-print-root .r-table-note")).to_contain_text("Prime 2 righe di 5")


def test_orientation_class_and_page_rule(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    _stub_print(page)
    _open_via_button(page)
    expect(page.locator(OVERLAY)).to_be_visible()

    page.locator("#rel-orientamento-orizzontale").check()
    page.get_by_role("button", name="Stampa / Salva PDF").click()
    page.wait_for_timeout(150)
    assert page.evaluate("document.documentElement.classList.contains('rel-print-landscape')") is True

    css_text = page.evaluate("fetch('/css/print.css').then(r => r.text())")
    assert "@page relazione-orizzontale" in css_text
    assert "html.rel-print-landscape" in css_text
    assert "page: relazione-orizzontale" in css_text


def test_options_and_cartiglio_persist_across_reload(page: Page, base_url: str) -> None:
    _load_demo(page, base_url)
    _stub_print(page)
    _open_via_button(page)
    expect(page.locator(OVERLAY)).to_be_visible()

    page.fill("#rel-cartiglio-progetto", "Progetto di prova")
    page.locator("#rel-preset-sintetica").check()
    page.wait_for_timeout(200)
    page.keyboard.press("Escape")
    expect(page.locator(OVERLAY)).to_be_hidden()

    page.reload()
    page.locator("#tool-title").wait_for(state="visible")
    # Reload restores the last inputs (DESIGN_SPEC P1) but does not itself re-run the tool --
    # `setValue()` on restore fires no "input"/"change" event, same as "Carica esempio"
    # (js/forms.js) -- Ctrl+Enter (WORKBENCH_SPEC §2, works anywhere, live on or off) forces it.
    page.keyboard.press("Control+Enter")
    page.locator("#r-group-verifiche").wait_for(state="visible")
    _stub_print(page)
    _open_via_button(page)
    expect(page.locator(OVERLAY)).to_be_visible()
    assert page.input_value("#rel-cartiglio-progetto") == "Progetto di prova"
    expect(page.locator("#rel-preset-sintetica")).to_be_checked()


def test_keyboard_only_focus_trap_and_escape_returns_focus(page: Page, base_url: str) -> None:
    _load_demo(page, base_url)
    _stub_print(page)
    trigger = page.get_by_role("button", name="Stampa relazione")
    trigger.click()
    expect(page.locator(OVERLAY)).to_be_visible()
    assert page.evaluate("document.activeElement.id") == "rel-overlay-title"

    for _ in range(40):
        page.keyboard.press("Tab")
        inside = page.evaluate("document.getElementById('relazione-overlay').contains(document.activeElement)")
        assert inside, "Tab must never move focus outside the modal overlay"

    page.keyboard.press("Escape")
    expect(page.locator(OVERLAY)).to_be_hidden()
    assert page.evaluate("document.activeElement.classList.contains('r-print-trigger')")


def test_no_overlay_chrome_in_print_media(page: Page, base_url: str) -> None:
    _load_demo(page, base_url)
    _stub_print(page)
    _open_via_button(page)
    expect(page.locator(OVERLAY)).to_be_visible()
    try:
        page.emulate_media(media="print")
        expect(page.locator(OVERLAY)).to_be_hidden()
    finally:
        page.emulate_media(media=None)


def test_mobile_390_no_horizontal_overflow(mobile_page: tuple[Page, PageCollectors], base_url: str) -> None:
    page, collectors = mobile_page
    page.add_init_script("window.print = () => {};")
    page.goto(f"{base_url}/#/demo-relazione")
    page.locator("#tool-title").wait_for(state="visible")
    page.get_by_role("tab", name="Dati").click()
    page.get_by_role("button", name="Carica esempio").click()
    page.get_by_role("tab", name="Risultati").click()
    page.locator("#r-group-verifiche").wait_for(state="visible")

    page.locator(".r-print-trigger").first.evaluate("(el) => el.click()")
    expect(page.locator(OVERLAY)).to_be_visible()
    page.wait_for_timeout(400)

    scroll_w = page.evaluate("document.documentElement.scrollWidth")
    client_w = page.evaluate("document.documentElement.clientWidth")
    assert scroll_w <= client_w + 1, f"horizontal overflow at 390px: scrollWidth {scroll_w} > clientWidth {client_w}"
    expect(page.locator(".rel-overlay-tabs")).to_be_visible()

    page.get_by_role("tab", name="Anteprima").click()
    expect(page.locator("#rel-preview-pane")).to_be_visible()
    expect(page.locator("#rel-options-pane")).to_be_hidden()

    assert collectors.console_errors == [], f"console.error calls: {collectors.console_errors}"
    assert collectors.page_errors == [], f"uncaught page errors: {collectors.page_errors}"
    assert csp_violations(page) == [], f"CSP violations: {csp_violations(page)}"


def test_zero_console_errors_desktop_full_flow(desktop_page: tuple[Page, PageCollectors], base_url: str) -> None:
    page, collectors = desktop_page
    page.add_init_script("window.print = () => {};")
    _load_demo(page, base_url)
    _open_via_button(page)
    expect(page.locator(OVERLAY)).to_be_visible()
    page.locator("#rel-preset-sintetica").check()
    page.locator("#rel-preset-completa").check()
    page.get_by_role("button", name="Ripristina predefiniti").click()
    page.get_by_role("button", name="Stampa / Salva PDF").click()
    page.wait_for_timeout(200)
    page.keyboard.press("Escape")
    expect(page.locator(OVERLAY)).to_be_hidden()

    assert collectors.console_errors == [], f"console.error calls: {collectors.console_errors}"
    assert collectors.page_errors == [], f"uncaught page errors: {collectors.page_errors}"
    assert csp_violations(page) == [], f"CSP violations: {csp_violations(page)}"
