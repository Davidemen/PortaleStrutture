"""WORKBENCH_SPEC §10/§11 -- "an exported report never depends on what happens to be open on
screen". `demo-relazione` (tests/e2e/_demo_tool.py) is a tiny synthetic tool with a deterministic
checks list, a nested scalar group and a paginated row table, so the "every group collapsed, the
checks folded, the filter on, a table on page 2" scenario does not depend on any real tool's
example data happening to be big enough to reach a second page."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import field_id, goto_tool, load_example

pytestmark = pytest.mark.e2e

REFUSAL_TEXT = "I risultati non corrispondono ai dati correnti — correggi i dati o ricalcola prima di stampare"


def _stub_print(page: Page) -> None:
    # `page.evaluate` auto-invokes an expression whose COMPLETION VALUE is itself a function -- a
    # bare "a; b = () => {...};" string's last statement evaluates to that arrow function, which
    # Playwright then calls immediately (flipping `__printed` before the real click ever happens).
    # Wrapping in a zero-arg arrow function makes the completion value `undefined` instead.
    page.evaluate("() => { window.__printed = false; window.print = () => { window.__printed = true; }; }")


def _click_print(page: Page) -> None:
    # WORKBENCH_SPEC §11: "Stampa relazione" now opens the report personalisation overlay instead
    # of printing straight away -- these §10 "always complete" tests exercise the overlay's OWN
    # default (Completa) "Stampa / Salva PDF" action, which prints the exact same complete
    # document (js/relazione-overlay.js `handleOverlayPrint`, untouched options = resolveOptions({})).
    page.get_by_role("button", name="Stampa relazione").click()
    page.locator("#relazione-overlay").wait_for(state="visible")
    page.get_by_role("button", name="Stampa / Salva PDF").click()
    page.locator("#relazione-print-root .print-cartiglio").wait_for(state="attached")
    page.keyboard.press("Escape")
    page.locator("#relazione-overlay").wait_for(state="hidden")


def test_print_is_complete_regardless_of_screen_state(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")

    # Screen state the report must NOT depend on: Verifiche collapsed (it defaults open), the
    # checks fold stays at its default (folded), "Solo non soddisfatte" on, the row table pushed
    # to its second page.
    page.locator("#r-group-verifiche").click()
    expect(page.locator("#r-group-verifiche")).to_have_attribute("aria-expanded", "false")
    page.get_by_role("button", name="Solo non soddisfatte").click()
    page.locator("#r-group-righe").click()
    page.locator("#r-group-righe-body").get_by_role("button", name="Pagina successiva").click()
    expect(page.locator("#r-group-righe-body .r-pager-status")).to_have_text("Pagina 2 di 3")
    page.locator("#r-group-righe").click()

    verifiche_expanded_before = page.locator("#r-group-verifiche").get_attribute("aria-expanded")
    filter_before = page.locator(".r-toolbar-filter").get_attribute("aria-pressed")
    scroll_before = page.evaluate("document.getElementById('results-pane').scrollTop")

    _stub_print(page)
    _click_print(page)
    assert page.evaluate("window.__printed") is True

    root = page.locator("#relazione-print-root")
    titles = root.locator(".r-group-title").all_inner_texts()
    for expected in ["Verifiche (5)", "Passaggi di calcolo", "Dettagli di calcolo", "Righe di dettaglio", "Avvisi"]:
        assert expected in titles, f"missing group title {expected!r} in printed titles {titles!r}"

    assert root.locator(".r-check").count() == 5, "every check must print, fold or no fold"
    assert root.locator(".r-table-print tbody tr").count() == 5, "every table row must print, paged or not"
    assert root.locator(".print-inputs .r-inputs-table tbody tr").count() == page.locator("#form-root .f-field").count()
    assert "Avviso di prova" in root.locator("p").all_inner_texts()[-1] or any(
        "Avviso di prova" in t for t in root.inner_text().splitlines()
    )

    # Nothing interactive: no buttons, no click-to-copy affordances.
    assert root.locator("button").count() == 0

    # Screen state is untouched by printing.
    assert page.locator("#r-group-verifiche").get_attribute("aria-expanded") == verifiche_expanded_before
    assert page.locator(".r-toolbar-filter").get_attribute("aria-pressed") == filter_before
    assert page.evaluate("document.getElementById('results-pane').scrollTop") == scroll_before


def test_print_refuses_when_inputs_invalid(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")

    page.fill(field_id("fattore"), "-1")
    page.locator(field_id("fattore")).blur()
    expect(page.locator(f"{field_id('fattore')}-error")).to_be_visible()

    _stub_print(page)
    page.get_by_role("button", name="Stampa relazione").click()
    error = page.locator("#run-error")
    expect(error).to_have_text(REFUSAL_TEXT)
    assert page.evaluate("window.__printed") is False, "an invalid/stale report must never reach window.print()"


def test_print_document_order_sketch_before_inputs(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    _stub_print(page)
    _click_print(page)

    order = page.evaluate(
        """() => {
            const root = document.getElementById('relazione-print-root');
            const schizzo = root.querySelector('.print-schizzo');
            const inputs = root.querySelector('.print-inputs');
            if (!schizzo || !inputs) return 'missing';
            return (schizzo.compareDocumentPosition(inputs) & Node.DOCUMENT_POSITION_FOLLOWING) ? 'schizzo-first' : 'inputs-first';
        }"""
    )
    assert order == "schizzo-first", "user rule: Schizzo prints BEFORE Dati di ingresso"


def test_print_inputs_row_count_matches_field_count(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    field_count = page.locator("#form-root .f-field").count()
    _stub_print(page)
    _click_print(page)

    row_count = page.locator("#relazione-print-root .print-inputs .r-inputs-table tbody tr").count()
    assert row_count == field_count, f"Dati di ingresso rows ({row_count}) must equal the tool's input fields ({field_count})"
    # Every numeric value is followed by its unit (never a bare number) -- muro-sostegno has no
    # table-input fields, so a bare "1" unit cell is fine, but the cell must exist for every row.
    assert page.locator("#relazione-print-root .print-inputs .r-inputs-table tbody tr td:nth-child(4)").count() == field_count
