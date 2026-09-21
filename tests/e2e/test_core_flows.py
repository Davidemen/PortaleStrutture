"""E2E flows 1-10 of DESIGN_SPEC §7. Most fail until shell/forms/results/charts land; the
assertions are written to fail with a clear message rather than a bare timeout."""
import pytest
from playwright.sync_api import Page, expect

from ._actions import CALCOLA, field_error_id, field_id, goto_tool, load_example, submit, tab_to_calcola
from ._collectors import PageCollectors, csp_violations, off_origin_requests

pytestmark = pytest.mark.e2e


def test_desktop_run(desktop_page: tuple[Page, PageCollectors], base_url: str) -> None:
    page, _ = desktop_page
    goto_tool(page, base_url, "vento-pressione")
    load_example(page)
    submit(page)

    verdict = page.locator(".r-verdict")
    expect(verdict).to_be_visible()
    highlight_rows = page.locator(".r-row[data-highlight]")
    assert highlight_rows.count() <= 3, f"expected <=3 marker rows, found {highlight_rows.count()}"

    # DESIGN_SPEC §7 test 1 pins the exact `1,523` figure measured on the *old* live app
    # (UI_BRIEF's own `p_h_kNm2=1.5230430659834242` quote); the redesigned tool's `example`
    # input (package E) produces a different golden case, so derive the expectation from the
    # row's own full-precision `title` instead of a stale literal (contractDeviations).
    value_cell = page.locator('#results-root .r-row[data-field="p_h_kNm2"] .r-cell-value')
    expect(value_cell).to_be_visible()
    full_precision = value_cell.get_attribute("title")
    assert full_precision, "expected the p(H) row to carry a full-precision title"
    displayed = value_cell.inner_text().strip()
    expected = f"{float(full_precision):.4g}".replace(".", ",")
    assert displayed == expected, f"expected 4-significant-digit {expected!r}, got {displayed!r}"
    assert full_precision not in page.locator("#results-root").inner_text(), (
        "full precision must never appear as visible text"
    )


def test_deep_link_boot(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/#/sisma-spettro")
    _assert_deep_link_state(page)
    page.reload()
    _assert_deep_link_state(page)


def _assert_deep_link_state(page: Page) -> None:
    page.locator("#tool-title").wait_for(state="visible")
    fields = page.locator("#form-root .f-field").count()
    assert fields > 0, "deep link boot must render the form fields on cold load and reload"
    current = page.locator('[data-tool="sisma-spettro"][aria-current="true"]')
    expect(current).to_have_count(1)


def test_keyboard_only(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/#/vento-pressione")
    outlines = tab_to_calcola(page)
    assert outlines, "no focus stops recorded before reaching Calcola"
    assert all(o != "0px" for o in outlines), f"a focused element had no visible outline: {outlines}"
    page.keyboard.press("Enter")
    expect(page.locator("#results-head")).to_be_focused()


def test_validation_flow(page: Page, base_url: str) -> None:
    # `as_m` has no `maximum` in the current CaricoFaldaInput schema (a missing backend hint,
    # out of static_next/tests/e2e scope -- flagged in contractDeviations), so the out-of-range
    # case here exercises `a` (angle of pitch, minimum 0 / maximum 90) instead; same client
    # validation mechanism (range message at the field, preserved value, summary link).
    goto_tool(page, base_url, "neve-carico-falda")
    page.locator(field_id("as_m")).fill("500")
    page.locator(field_id("topografia")).select_option("Normale")
    pitch = page.locator(field_id("a"))
    pitch.fill("120")
    submit(page)

    error = page.locator(field_error_id("a"))
    expect(error).to_be_visible()
    expect(pitch).to_have_attribute("aria-invalid", "true")
    expect(page.locator('#error-summary a[href="#field-a"]')).to_have_count(1)
    assert pitch.input_value() == "120", "the invalid value must be preserved, not cleared"

    pitch.fill("10")
    page.locator(field_id("comune")).fill("Milano")
    page.locator(field_id("zona")).select_option("II")
    submit(page)
    expect(page.locator(field_id("comune"))).to_have_attribute("aria-invalid", "true")
    expect(page.locator(field_id("zona"))).to_have_attribute("aria-invalid", "true")
    assert page.locator("#error-summary").locator("li").count() >= 1


def test_example_and_persistence(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "neve-carico-falda")
    load_example(page)
    submit(page)
    remembered = page.locator(field_id("as_m")).input_value()

    page.reload()
    restored = page.locator(field_id("as_m"))
    expect(restored).to_have_value(remembered)

    page.goto(f"{base_url}/#/neve-carico-falda?as_m=350")
    expect(page.locator(field_id("as_m"))).to_have_value("350")


def test_mobile_flow(mobile_page: tuple[Page, PageCollectors], base_url: str) -> None:
    page, _ = mobile_page
    page.goto(f"{base_url}/")

    picker = page.locator("details.app-picker")
    expect(picker).to_be_visible()
    # `> summary` only: the tool index (nested `<details class="ti-group">`, each with its own
    # `<summary>`) is moved inside the picker at this breakpoint (layout.js), so an unscoped
    # "summary" locator is ambiguous.
    picker.locator("> summary").click()
    picker.get_by_role("button", name="Vento", exact=False).first.click()

    load_example(page)
    submit(page)

    expect(page.locator("#app")).to_have_attribute("data-pane", "risultati")
    expect(page.locator("#results-head")).to_be_focused()

    overflow = page.evaluate("document.body.scrollWidth - document.body.clientWidth")
    assert overflow <= 0, f"page scrolls horizontally by {overflow}px at 390px"

    # Only elements actually visible right now: we're on the "Risultati" tab, so `#form-pane`
    # (and everything in it) is legitimately `hidden` and would report a 0px rect.
    tap_targets = page.locator(".ti-item, #form-actions button, #form-root .f-field input, #form-root .f-field select")
    heights = tap_targets.evaluate_all("nodes => nodes.filter(n => n.getBoundingClientRect().height > 0).map(n => n.getBoundingClientRect().height)")
    undersized = [h for h in heights if h < 44]
    assert not undersized, f"tap targets below 44px: {undersized}"


def test_tablet_layout(tablet_page: tuple[Page, PageCollectors], base_url: str) -> None:
    """720-1099px: results sit below the form in the same column, never on top of it
    (DESIGN_SPEC §2) -- regression for the two panes sharing one grid cell."""
    page, _ = tablet_page
    goto_tool(page, base_url, "vento-pressione")
    load_example(page)
    submit(page)

    form_box = page.locator("#form-pane").bounding_box()
    results_box = page.locator("#results-pane").bounding_box()
    assert form_box and results_box, "expected both #form-pane and #results-pane to have a layout box"
    assert form_box["y"] + form_box["height"] <= results_box["y"] + 1, (
        f"form ({form_box}) and results ({results_box}) overlap at the tablet breakpoint"
    )


def test_chart_present(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "sisma-spettro")
    load_example(page)
    submit(page)
    series = page.locator("svg path[data-series]")
    expect(series).to_have_count(2)
    rows = page.locator(".r-table-scroll tbody tr")
    assert rows.count() == 81, f"expected 81 spectrum rows, found {rows.count()}"

    goto_tool(page, base_url, "vento-cpe-rettangolare")
    load_example(page)
    submit(page)
    expect(page.locator("svg")).to_have_count(0)


def test_print_media(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "vento-pressione")
    load_example(page)
    submit(page)
    # "Stampa relazione" builds the print-only cartiglio (print.js only inserts it on demand,
    # per DESIGN_SPEC §3) before the print stylesheet reshapes the sheet for @media print.
    page.get_by_role("button", name="Stampa relazione").click()
    page.emulate_media(media="print")

    cartiglio = page.locator(".print-cartiglio")
    expect(cartiglio.first).to_be_visible()
    cartiglio_text = cartiglio.first.inner_text()
    assert "Pressione" in cartiglio_text, f"expected the tool title in the cartiglio, got: {cartiglio_text!r}"
    assert "standard" in cartiglio_text or "foglio Excel" in cartiglio_text, "mode line must always print"
    expect(page.locator("#tool-index")).to_be_hidden()
    expect(page.get_by_role("button", name=CALCOLA)).to_be_hidden()


def test_copy_csv(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "sisma-spettro")
    load_example(page)
    submit(page)
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Scarica CSV").click()
    download = download_info.value
    path = download.path()
    assert path is not None
    content = path.read_bytes().decode("utf-8-sig")
    first_line = content.splitlines()[0]
    assert ";" in first_line, f"expected ';'-separated CSV, got header: {first_line!r}"
    assert "," in content, "expected an it-IT decimal comma somewhere in the exported values"


def test_no_console_errors_no_csp(desktop_page: tuple[Page, PageCollectors], base_url: str) -> None:
    page, collectors = desktop_page
    page.goto(f"{base_url}/")
    tool_names = page.evaluate(
        "fetch('/api/tools').then(r => r.json()).then(list => list.map(t => t.name))"
    )
    assert tool_names, "GET /api/tools returned no tools to walk"

    for name in tool_names:
        page.goto(f"{base_url}/#/{name}")
        page.locator("#tool-title").wait_for(state="visible")

    assert collectors.console_errors == [], f"console.error calls: {collectors.console_errors}"
    assert collectors.page_errors == [], f"uncaught page errors: {collectors.page_errors}"
    assert csp_violations(page) == [], f"CSP violations: {csp_violations(page)}"
    offsite = off_origin_requests(collectors, base_url)
    assert offsite == [], f"requests left {base_url}: {offsite}"

    heading_count = page.evaluate("document.querySelectorAll('h1').length")
    assert heading_count == 1, f"expected exactly one h1, found {heading_count}"
    live_regions = page.evaluate("document.querySelectorAll('[aria-live],[role=alert]').length")
    assert live_regions == 3, f"expected 3 live regions, found {live_regions}"
