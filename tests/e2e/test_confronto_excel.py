"""E2E coverage for WORKBENCH_SPEC.md §13.3: the "Confronta con Excel" results-toolbar toggle and
its panel. `muro-sostegno` has the `legacy_compat` input (a real, deterministic golden case);
`demo-relazione` (tests/e2e/_demo_tool.py) has no such field, so its own toolbar must never grow
the toggle -- proves the button is schema-driven, not tool-name-driven.
"""
from __future__ import annotations

import json
import re
import time
from urllib.parse import quote

import pytest
from playwright.sync_api import Page, Response, Route, expect

from ._actions import field_id, goto_tool, load_example

pytestmark = pytest.mark.e2e


def _open_compare(page: Page) -> None:
    page.locator(".cf-toggle").click()
    page.locator("#confronto-panel .cf-summary").wait_for(state="visible")
    # the panel starts with the loading placeholder; wait for the real result to replace it.
    expect(page.locator("#confronto-panel .cf-summary")).not_to_have_text("Confronto in corso…", timeout=10_000)


# -- visibility: schema-driven, not tool-name-driven ---------------------------------------------


def test_toggle_shown_only_when_legacy_compat_present(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    expect(page.locator(".cf-toggle")).to_have_count(1)

    goto_tool(page, base_url, "demo-relazione")
    page.fill(field_id("fattore"), "2")
    page.locator(field_id("fattore")).blur()
    page.wait_for_timeout(500)
    expect(page.locator(".r-toolbar")).to_be_visible()
    expect(page.locator(".cf-toggle")).to_have_count(0)


def test_toggle_is_aria_pressed_and_panel_toggles_with_it(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    toggle = page.locator(".cf-toggle")
    expect(toggle).to_have_attribute("aria-pressed", "false")
    expect(page.locator("#confronto-panel")).to_have_count(0)

    toggle.click()
    expect(toggle).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#confronto-panel")).to_have_count(1)

    toggle.click()
    expect(toggle).to_have_attribute("aria-pressed", "false")
    expect(page.locator("#confronto-panel")).to_have_count(0)


def test_panel_survives_a_live_rerender(page: Page, base_url: str) -> None:
    """The toolbar (and so `.cf-toggle`) is rebuilt on every render -- the ON state must be
    re-applied, not reset, across a live recalculation triggered by plain typing."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    page.locator(".cf-toggle").click()
    expect(page.locator(".cf-toggle")).to_have_attribute("aria-pressed", "true")

    page.locator(field_id("b_valle_m")).fill("2.10")  # no Enter/Calcola: live recalculation only
    page.wait_for_timeout(800)
    expect(page.locator(".cf-toggle")).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#confronto-panel")).to_have_count(1)


# -- panel content ---------------------------------------------------------------------------


def test_panel_placed_directly_under_sintesi(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    _open_compare(page)
    order = page.evaluate(
        """() => {
          const pane = document.getElementById('results-pane');
          const ids = [...pane.children].map(el => el.id);
          return ids;
        }"""
    )
    assert order.index("sintesi") < order.index("confronto-panel") < order.index("results-root"), order


def test_summary_sentence_and_diff_table(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    _open_compare(page)

    summary = page.locator("#confronto-panel .cf-summary").inner_text()
    assert re.search(r"\d+ valor(e diverso|i diversi)", summary), summary
    # a verdict that differs and a utilisation that merely moves are different news, and the sentence
    # must always say which is which (on this example the minimum-reinforcement checks DO change
    # verdict: the sheet chose the bars without the code minimum)
    assert re.search(r"(nessuna verifica cambia esito|\d+ verific(a cambia|he cambiano) esito)", summary), summary
    assert re.search(r"\d+ verific(a|he) con valore diverso", summary), summary
    assert re.search(r"\d+ correzion(e coinvolta|i coinvolte)", summary), summary

    # 224 differing values: the table is folded (it must never bury the results); open it
    fold = page.locator("#confronto-panel details.cf-fold", has_text="Valori diversi")
    expect(fold).to_have_count(1)
    assert fold.evaluate("d => d.open") is False
    fold.locator("summary").click()
    rows = page.locator("#confronto-panel .cf-table tbody tr")
    expect(rows.first).to_be_visible()
    header_cells = page.locator("#confronto-panel .cf-table thead th").all_inner_texts()
    assert header_cells == ["Grandezza", "Standard", "Excel", "Δ", "Δ %", "Correzione"]

    # at least one row's "Correzione" cell links back into the register, filtered to that id
    link = page.locator("#confronto-panel .cf-table a").first
    expect(link).to_be_visible()
    href = link.get_attribute("href")
    assert href.startswith("#/registro?id=")


def test_checks_changed_show_icon_word_and_both_values(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    _open_compare(page)

    # twelve checks whose value moves but whose verdict stands: listed, behind their own disclosure
    fold = page.locator("#confronto-panel details.cf-fold", has_text="Verifiche con valore diverso")
    fold.locator("summary").click()
    check_rows = page.locator("#confronto-panel .cf-check")
    expect(check_rows.first).to_be_visible()
    first = check_rows.first
    expect(first.locator(".cf-check-name")).to_be_visible()
    verdicts = first.locator(".cf-check-verdict")
    expect(verdicts).to_have_count(2)
    for i in range(2):
        text = verdicts.nth(i).inner_text()
        assert "Soddisfatta" in text or "Non soddisfatta" in text or "—" in text, text


def test_many_differences_capped_with_footnote(page: Page, base_url: str) -> None:
    """The golden muro-sostegno case has well over 200 output-leaf differences between the two
    modes (backend cap `confronto.py::MAX_DIFFERENZE`); the panel must say so."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    _open_compare(page)
    rows = page.locator("#confronto-panel .cf-table tbody tr")
    expect(rows).to_have_count(200)
    note = page.locator("#confronto-panel .cf-note", has_text="Mostrate le prime")
    expect(note).to_be_visible()
    expect(note).to_have_text(re.compile(r"Mostrate le prime 200 di \d+\."))


def test_attribution_notes_partial_and_non_isolable(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §13 addendum: `confronto.attribuzione` (exact-for-these-inputs attribution,
    `confronto.py::attribuisci_per_singola_correzione`, 3s budget). Real muro-sostegno runs finish
    well inside that budget with everything evaluated, so both notes are mocked here -- a real,
    unmodified compare response is fetched then re-fulfilled with only `attribuzione` overridden,
    keeping the rest of the panel's content (differenze/verifiche/summary) genuine."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    non_isolable_id = "muro-sostegno/coefficienti-resistenza-mancanti"

    def mock_attribuzione(route: Route) -> None:
        response = route.fetch()
        body = response.json()
        body["confronto"]["attribuzione"] = {"correzioni_valutate": 3, "completa": False, "non_valutabili": [non_isolable_id]}
        route.fulfill(response=response, json=body)

    page.route("**/api/tools/muro-sostegno/compare", mock_attribuzione)
    page.locator(".cf-toggle").click()
    expect(page.locator("#confronto-panel .cf-summary")).not_to_have_text("Confronto in corso…", timeout=10_000)

    partial_note = page.locator("#confronto-panel .cf-note", has_text="Attribuzione parziale")
    expect(partial_note).to_have_text("Attribuzione parziale: non tutte le correzioni sono state provate.")

    isolare_note = page.locator("#confronto-panel .cf-note", has_text="non si possono isolare")
    expect(isolare_note).to_be_visible()
    link = isolare_note.locator("a")
    expect(link).to_have_count(1)
    expect(link).to_have_text(non_isolable_id)
    assert link.get_attribute("href") == f"#/registro?id={quote(non_isolable_id, safe='')}"


def test_confronto_not_part_of_printed_report(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    _open_compare(page)
    page.emulate_media(media="print")
    expect(page.locator("#confronto-panel")).not_to_be_visible()
    page.emulate_media(media="screen")


# -- stale-while-recomputing / never-stale (same rules as live calculation) ---------------------


def test_stale_compare_response_never_overwrites_newer(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §13.3 "through the same debounce/queue as live calculation" + §9's own
    stale-response rule applied to the comparison: a delayed compare response for an EARLIER
    input must never land after -- and so never overwrite -- a fresher one."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    _open_compare(page)

    responses: list[Response] = []

    def collect(response: Response) -> None:
        if response.request.method == "POST" and response.url.endswith("/api/tools/muro-sostegno/compare"):
            responses.append(response)

    page.on("response", collect)

    def delay_first_value_only(route: Route) -> None:
        body = route.request.post_data or ""
        if '"h_muro_m":3.5' in body:
            time.sleep(1.5)
        route.continue_()

    page.route("**/api/tools/muro-sostegno/compare", delay_first_value_only)

    height = page.locator(field_id("h_muro_m"))
    height.fill("3.5")  # debounces, then the route delays ITS compare response by 1.5s
    page.wait_for_timeout(500)  # the compare request for 3.5 is now in flight (and delayed)
    height.fill("2.8")  # a second run-request follows once the (undelayed) /run for 3.5 settles

    page.wait_for_timeout(3_000)
    assert len(responses) == 2, f"expected exactly 2 compare responses (3.5 then 2.8), got {len(responses)}"

    last_body = json.loads(responses[-1].text())
    last_confronto = last_body["confronto"]
    rendered = page.locator("#confronto-panel .cf-summary").inner_text()
    assert str(last_confronto["totale_differenze"]) in rendered, (
        f"rendered summary ({rendered!r}) must reflect the LAST-settled compare response, "
        f"not the delayed one for h_muro_m=3.5"
    )
    assert not page.locator("#confronto-panel").evaluate("el => el.classList.contains('cf-panel--stale')")


# -- non-live tool: only on "Calcola" -----------------------------------------------------------


def test_non_live_tool_only_compares_on_calcola(page: Page, base_url: str) -> None:
    """A table-input tool with > 200 rows forces live off (WORKBENCH_SPEC §2); the comparison
    must follow the SAME rule -- typing alone must not trigger a new compare request."""
    goto_tool(page, base_url, "fond-plinto-isolato")
    load_example(page)
    page.locator(".r-toolbar").wait_for(state="visible")
    if page.locator(".cf-toggle").count() == 0:
        pytest.skip("fond-plinto-isolato has no legacy_compat in this build")
    page.locator(".cf-toggle").click()
    expect(page.locator("#confronto-panel .cf-summary")).not_to_have_text("Confronto in corso…", timeout=10_000)

    requests_before = []

    def collect(route: Route) -> None:
        requests_before.append(route.request)
        route.continue_()

    page.route("**/api/tools/fond-plinto-isolato/compare", collect)
    page.locator(field_id("ax_m")).fill("2.10")
    page.wait_for_timeout(600)
    assert len(requests_before) == 0, "typing alone must not fire a compare request when live is off"
