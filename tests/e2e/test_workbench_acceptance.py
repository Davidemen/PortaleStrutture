"""E2E coverage for WORKBENCH_SPEC.md §9 acceptance items not already exercised by
test_core_flows.py / test_ui_polish.py / test_table_input.py / test_midas_import.py.
"""
from __future__ import annotations

import json
import time

import pytest
from playwright.sync_api import Page, Response, Route, expect

from ._actions import field_id, goto_tool, load_example, submit

pytestmark = pytest.mark.e2e


def test_live_update_flashes_within_one_second(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §2/§9: "typing in a field updates a highlighted result within 1 s without
    pressing anything and flashes it" -- the 300ms debounce + a local fetch must both land well
    inside the 1s budget, and the changed cell must carry `data-changed` (results-diff.js
    `markChanged`, marker-yellow fade) while it does."""
    goto_tool(page, base_url, "vento-pressione")
    load_example(page)
    expect(page.locator("#sintesi .r-si-figure").first).to_be_visible()

    altitude = page.locator(field_id("altezza_edificio_m"))
    altitude.fill("300")
    # No Enter, no Calcola click: WORKBENCH_SPEC §2's whole premise is that live calculation
    # reacts to input alone.
    page.locator("[data-changed]").first.wait_for(state="attached", timeout=1_000)


def test_invalid_input_keeps_previous_results_dimmed(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §2/§9: "an invalid value keeps the previous results dimmed with the chip"
    -- the last good render must stay in the DOM (never blanked to the empty state) with
    `.r-sheet--stale` and the "dati non validi" chip, and the field itself shows the inline error."""
    goto_tool(page, base_url, "vento-pressione")
    load_example(page)
    expect(page.locator("#sintesi .r-si-figure").first).to_be_visible()
    # Scoped to the figures, not the whole `#sintesi`: the stale chip PREPENDS itself into
    # `#sintesi` once invalid (below), so comparing the container's full text would always differ
    # by exactly the chip and defeat the "results are untouched" assertion this is making.
    good_figures_text = page.locator("#sintesi .r-si-figures").inner_text()

    altitude = page.locator(field_id("altezza_edificio_m"))
    altitude.fill("-50")  # altezza_edificio_m has `exclusiveMinimum: 0` (must be > 0), no maximum

    expect(altitude).to_have_attribute("aria-invalid", "true")
    expect(page.locator(".r-si-chip")).to_contain_text("dati non validi")
    expect(page.locator("#results-root.r-sheet--stale")).to_have_count(1)
    # The PREVIOUS good render is still the one on screen, not an emptied sheet.
    assert page.locator("#sintesi .r-si-figures").inner_text() == good_figures_text, (
        "invalid input must not blank or change the last good results"
    )


def test_stale_response_never_overwrites_newer(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §2/§9: "a stale response never overwrites a newer one (test with delayed
    routes)". live.js serialises runs by queueing rather than aborting (documented contract
    deviation -- see the final report): a run already in flight is never cancelled, but nothing
    newer is ever sent before it settles, so responses can never complete out of order. This test
    delays the FIRST run's response well past the second edit and asserts the sheet ends up
    showing the run that finishes LAST (the newer one), not the delayed one."""
    goto_tool(page, base_url, "vento-pressione")
    load_example(page)
    expect(page.locator("#sintesi .r-si-figure").first).to_be_visible()

    responses: list[Response] = []

    def collect_run_responses(response: Response) -> None:
        if response.request.method == "POST" and response.url.endswith("/api/tools/vento-pressione/run"):
            responses.append(response)

    page.on("response", collect_run_responses)

    def delay_first_value_only(route: Route) -> None:
        body = route.request.post_data or ""
        if '"altezza_edificio_m":111' in body:
            time.sleep(1.5)
        route.continue_()

    page.route("**/api/tools/vento-pressione/run", delay_first_value_only)

    altitude = page.locator(field_id("altezza_edificio_m"))
    altitude.fill("111")  # debounces at +300ms, then the route delays ITS response by 1.5s
    page.wait_for_timeout(500)  # the request for 111 is now in flight (and delayed)
    altitude.fill("222")  # queued behind it (live.js "one request in flight" rule), not delayed

    # Give both requests (the delayed 111 + the queued, fast 222) time to fully settle.
    page.wait_for_timeout(2_500)
    assert altitude.input_value() == "222"
    assert len(responses) == 2, f"expected exactly 2 run responses (111 then 222), got {len(responses)}"

    first_value = json.loads(responses[0].text())["data"]["p_h_kNm2"]
    last_value = json.loads(responses[1].text())["data"]["p_h_kNm2"]
    assert first_value != last_value, "111 and 222 must produce different p(H) values for this to be a real race"

    rendered_title = page.locator('#sintesi .r-si-figure[data-field="p_h_kNm2"] .r-si-figure-value').get_attribute("title")
    assert rendered_title == str(last_value), (
        f"rendered figure ({rendered_title}) must match the LAST-settled response ({last_value}), "
        f"not the delayed first one ({first_value})"
    )


def test_wall_form_height_budget(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §3/§9: "retaining wall: form ≤ 1100 px ... at first render", i.e. WITH all
    sections collapsed but the first (WORKBENCH_SPEC §3) -- deliberately not `goto_tool`, which
    expands every section for the other tests' convenience and would defeat this measurement."""
    page.goto(f"{base_url}/#/muro-sostegno")
    page.locator("#tool-title").wait_for(state="visible")
    load_example(page)
    # The run itself is async; `#results-head` is intentionally always screen-hidden now (finding
    # E), so the verdict line is the real "a run has landed" signal for this wait.
    page.locator("#sintesi .r-si-verdict").wait_for(state="visible")
    height = page.evaluate("document.getElementById('form-root').scrollHeight")
    assert height <= 1100, f"muro-sostegno Dati column is {height}px tall, budget is 1100px"


def test_wall_results_height_budget(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC #9/finding J: retaining-wall RESULTS <=900px at first render. Closed by:
    the Sintesi's sketch moving BESIDE the verdict instead of stacked below it (finding B), the
    toolbar collapsing from 3 tall buttons + a jump-link strip to one 32px row (finding E), the
    repeated tool title going screen-hidden (finding E), the Verifiche fold tightening from 5 to
    the failed checks + the 3 highest utilisations (finding J), and a handful of group-header/
    check-row density trims -- previously xfail at ~1437px, now measured ~891px."""
    page.goto(f"{base_url}/#/muro-sostegno")
    page.locator("#tool-title").wait_for(state="visible")
    load_example(page)
    # `#results-head` is intentionally always screen-hidden now (finding E) -- the verdict line
    # is the real "a run has landed" signal for a sighted assertion like this one.
    page.locator("#sintesi .r-si-verdict").wait_for(state="visible")
    # sintesi.js's sketch views are a dynamic import + async render, a tick or two after the run
    # itself resolves -- wait for one so the measurement below reflects the REAL first render,
    # not a premature, incomplete DOM caught mid-render.
    page.locator("#sintesi .r-si-sketch svg").first.wait_for(state="attached")
    total = page.evaluate(
        "document.getElementById('sintesi').scrollHeight + document.getElementById('results-root').scrollHeight"
    )
    assert total <= 900, f"muro-sostegno results are {total}px tall, budget is 900px"


def test_footing_sketch_widens_when_b_grows(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §7/§9: "the footing sketch widens when B grows" -- fond-plinto-isolato has
    `live=False` (a Calcola button), so this also exercises "Calcola" explicitly."""
    goto_tool(page, base_url, "fond-plinto-isolato")
    load_example(page)
    # sintesi.js's `appendSketches` dynamically imports js/sketch.js and renders asynchronously,
    # a tick or two after "Carica esempio"'s own click handler returns.
    page.locator('#sintesi figure:has-text("Pianta") svg').wait_for(state="attached")

    def pianta_view_box() -> str | None:
        return page.evaluate(
            """() => {
                const fig = [...document.querySelectorAll('#sintesi figure')]
                    .find(f => f.querySelector('figcaption')?.textContent.trim() === 'Pianta');
                return fig ? fig.querySelector('svg').getAttribute('viewBox') : null;
            }"""
        )

    before = pianta_view_box()
    assert before, "expected a 'Pianta' sketch view after loading the example"
    before_width = float(before.split()[2])

    by_field = page.locator(field_id("by_m"))
    by_field.fill(str(float(by_field.input_value()) * 2))
    submit(page)
    page.wait_for_timeout(300)

    after = pianta_view_box()
    assert after, "expected the 'Pianta' sketch view to survive the recalculation"
    after_width = float(after.split()[2])
    assert after_width > before_width, f"Pianta viewBox did not widen: {before!r} -> {after!r}"


def test_palette_ctrl_k_search_opens_tool(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §6/§9: "Ctrl+K -> type 'punz' -> Enter opens the punching tool"."""
    page.goto(f"{base_url}/#/")
    page.locator("#home-search").wait_for(state="visible")
    page.keyboard.press("Control+k")
    palette_input = page.locator("#palette-input")
    expect(palette_input).to_be_visible()
    palette_input.fill("punz")
    expect(page.locator(".palette-option").first).to_contain_text("punzonamento")
    page.keyboard.press("Enter")
    expect(page).to_have_url(f"{base_url}/#/ca-punzonamento")
    expect(page.locator('[data-tool="ca-punzonamento"][aria-current="true"]').first).to_be_visible()


def test_favourites_persist_across_reload(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §6/§9: "favourites persist across reload" (localStorage `sm.nav.fav`)."""
    page.goto(f"{base_url}/#/")
    page.locator("#home-search").wait_for(state="visible")
    page.get_by_role("button", name="Aggiungi Pressione del vento ai preferiti").click()
    # The star's accessible name flips ("Aggiungi" -> "Rimuovi") the instant it toggles, so the
    # post-click assertion re-queries by the NEW name rather than reusing the pre-click locator.
    toggled = page.get_by_role("button", name="Rimuovi Pressione del vento dai preferiti")
    expect(toggled.first).to_have_attribute("aria-pressed", "true")

    page.reload()
    page.locator("#home-search").wait_for(state="visible")
    # The favourited tool now shows twice (its own "Preferiti" card + its category card), both
    # toggled together -- `.first` avoids a strict-mode ambiguity, not a real choice between them.
    reloaded_button = page.get_by_role("button", name="Rimuovi Pressione del vento dai preferiti").first
    expect(reloaded_button).to_be_visible()
    preferiti = page.locator("section.home-section", has=page.get_by_role("heading", name="Preferiti"))
    expect(preferiti.get_by_text("Pressione del vento", exact=True)).to_be_visible()


def test_mobile_bottom_bar_shows_verdict(mobile_page: tuple[Page, object], base_url: str) -> None:
    """WORKBENCH_SPEC §1/§9: "the bottom bar on mobile shows the verdict"."""
    page, _ = mobile_page
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)

    bottom_bar = page.locator("#bottom-bar")
    expect(bottom_bar).to_be_visible()
    expect(bottom_bar).to_contain_text("verific")  # "Tutte le verifiche soddisfatte" / "N verifiche non soddisfatte"


def test_live_off_for_large_table(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §2/§9: "live is off for a 300-row table and 'Calcola' appears" (>200 rows
    in ANY table input, per live.js `MAX_LIVE_TABLE_ROWS`), against the e2e `demo-tabella` tool
    (DESIGN_SPEC §4b) rather than a real >200-row production tool."""
    goto_tool(page, base_url, "demo-tabella")
    expect(page.get_by_role("button", name="Calcola")).to_have_count(0)  # live is on for a small table

    page.get_by_text("Incolla da Excel", exact=True).click()
    rows = "\n".join(f"{i}\t{10 + i}" for i in range(300))
    page.locator("textarea").fill(f"z\tE\n{rows}\n")
    page.get_by_role("button", name="Applica").click()

    expect(page.get_by_role("button", name="Calcola")).to_be_visible()
