"""E2E coverage for docs/ui/REVIEW_FABLE_2026-09-21.md (the "staging UI fixer" findings + the
orchestrator's own list at the end of the review). Findings already covered by an existing test
file are not repeated here (M1/M2/M5/M6 sketch quality -> test_sketch_quality.py, §10/§11 report
export -> test_report_print.py, chart -> test_ui_polish.py, header search removal -> the
"H" section of test_workbench_fixes.py)."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from strutture.shared.tool import discover

from ._actions import goto_tool, load_example, submit

pytestmark = pytest.mark.e2e

ALL_TOOL_NAMES = sorted(discover().keys())


# -- Finding 1 (P0): stirrups unfilled, bars stay filled ---------------------------------------


def test_stirrup_outline_unfilled_while_bars_stay_filled(page: Page, base_url: str) -> None:
    """fond-trave-collegamento draws the stirrup as a Rettangolo(stile="armatura") and the
    longitudinal bars as Barre(stile="armatura") -- only the bars may be filled ink."""
    goto_tool(page, base_url, "fond-trave-collegamento")
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")

    result = page.evaluate(
        """() => {
            const svg = document.querySelector('.r-si-sketch svg');
            const staffa = svg.querySelector('rect.sk-armatura');
            const barCircles = Array.from(svg.querySelectorAll('g.sk-armatura > circle'));
            return {
                staffaFill: staffa ? getComputedStyle(staffa).fill : null,
                staffaStroke: staffa ? getComputedStyle(staffa).stroke : null,
                barCount: barCircles.length,
                barFills: barCircles.map((c) => getComputedStyle(c).fill),
            };
        }"""
    )
    assert result["staffaFill"] == "none", f"stirrup rect must be unfilled, got {result['staffaFill']!r}"
    assert result["staffaStroke"] not in (None, "none", ""), "stirrup rect must keep a visible outline stroke"
    assert result["barCount"] > 0, "expected at least one longitudinal bar circle"
    assert all(f != "none" for f in result["barFills"]), f"bar circles must stay filled: {result['barFills']}"


# -- Finding 2 (P0): every sketch text is fill-opacity 1 ----------------------------------------


@pytest.mark.parametrize("tool_name", ["muro-sostegno", "fond-plinto-isolato", "neve-accumulo"])
def test_every_sketch_text_is_fully_opaque(page: Page, base_url: str, tool_name: str) -> None:
    goto_tool(page, base_url, tool_name)
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")

    opacities = page.evaluate(
        "() => Array.from(document.querySelectorAll('.r-si-sketch svg text')).map(t => getComputedStyle(t).fillOpacity)"
    )
    assert opacities, f"{tool_name}: expected at least one sketch text"
    offending = [o for o in opacities if float(o) < 0.999]
    assert not offending, f"{tool_name}: text with fill-opacity < 1: {offending}"


# -- Finding 4 (P0): evidenza tint lets underlying shapes show through --------------------------


def test_evidenza_perimeter_is_tinted_not_opaque(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "ca-punzonamento")
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")

    opacity = page.evaluate(
        """() => {
            const shape = document.querySelector('.r-si-sketch svg .sk-evidenza');
            return shape ? getComputedStyle(shape).fillOpacity : null;
        }"""
    )
    if opacity is None:
        pytest.skip("ca-punzonamento's example draws no sk-evidenza perimeter")
    assert 0 < float(opacity) < 1, f"evidenza fill-opacity must be a tint, not opaque or invisible: {opacity}"


# -- Finding 6 (P0): printed cartiglio label/value pairs in order -------------------------------


def test_print_cartiglio_label_value_pairs_in_order(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    page.evaluate("() => { window.print = () => {}; }")
    page.get_by_role("button", name="Stampa relazione").click()
    page.locator("#relazione-overlay").wait_for(state="visible")
    page.get_by_role("button", name="Stampa / Salva PDF").click()
    page.locator("#relazione-print-root .print-cartiglio").wait_for(state="attached")

    pairs = page.evaluate(
        """() => {
            const dl = document.querySelector('#relazione-print-root .print-cartiglio-meta');
            const children = Array.from(dl.children);
            const out = [];
            for (let i = 0; i < children.length; i += 2) {
                out.push([children[i].tagName, children[i + 1] ? children[i + 1].tagName : null]);
            }
            return out;
        }"""
    )
    assert pairs, "expected at least one cartiglio dt/dd pair"
    for term_tag, value_tag in pairs:
        assert term_tag == "DT", f"expected a dt/dd pair in order, got {pairs}"
        assert value_tag == "DD", f"expected a dt/dd pair in order, got {pairs}"


# -- Finding 8 (P0) + "Carica esempio for every tool" -------------------------------------------


@pytest.mark.parametrize("tool_name", ALL_TOOL_NAMES)
def test_example_runs_successfully_with_no_underscore_in_verdict_text(page: Page, base_url: str, tool_name: str) -> None:
    """Every registered tool's own golden example must run to a successful result from the UI
    (this is also the acciaio-resistenza-incendio list-input regression test: it used to fail here
    with a server-side "tempi_min: Input should be a valid tuple" 422). Zero native browser
    alert()/confirm()/prompt() dialogs, and no raw "_" leaks into any check name/clause/detail."""
    dialogs: list[str] = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    goto_tool(page, base_url, tool_name)
    load_example(page)
    page.wait_for_timeout(400)
    # sisma-spettro/vento-pressione (live) can queue a second run right behind "Carica esempio" --
    # settle on whichever finished last rather than racing a still-in-flight one.
    page.wait_for_timeout(600)

    run_error = page.locator("#run-error")
    assert run_error.is_hidden() or run_error.inner_text() == "", f"{tool_name}: run-error visible: {run_error.inner_text()}"

    invalid_fields = page.locator('#form-root [aria-invalid="true"]').count()
    assert invalid_fields == 0, f"{tool_name}: {invalid_fields} field(s) still aria-invalid after loading the example"

    sintesi_html = page.locator("#sintesi").inner_html()
    assert len(sintesi_html) > 20, f"{tool_name}: Sintesi is empty after loading the example"

    texts = page.evaluate(
        """() => Array.from(document.querySelectorAll('.r-check-name, .r-check-clause, .r-check-detail, .r-si-eta-name'))
            .map(el => el.textContent || '')"""
    )
    offending = [t for t in texts if "_" in t]
    assert not offending, f"{tool_name}: raw underscore in verdict/check text: {offending}"

    assert dialogs == [], f"{tool_name}: unexpected native dialog(s): {dialogs}"


# -- List-input widget (orchestrator finding): acciaio-resistenza-incendio ----------------------


def test_list_input_widget_for_array_of_scalars(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "acciaio-resistenza-incendio")
    page.wait_for_timeout(300)

    field = page.locator('.f-field[data-field="tempi_min"]')
    expect(field).to_have_attribute("data-kind", "list")
    chip_count = field.locator(".f-list-chip").count()
    assert chip_count > 1, "expected the schema default (24 values) prefilled as chips"

    # decimal comma + mixed separators
    text_input = field.locator(".f-list-input input")
    text_input.fill("5; 10; 15,5")
    page.wait_for_timeout(150)
    chips = field.locator(".f-list-chip:not(.f-list-chip--invalid)").all_inner_texts()
    assert chips == ["5", "10", "15,5"], f"unexpected parsed chips: {chips}"

    # invalid token -> Italian error message, chip flagged
    text_input.fill("5; abc; 10")
    page.wait_for_timeout(150)
    invalid_chip = field.locator(".f-list-chip--invalid")
    expect(invalid_chip).to_have_text("abc")
    error = field.locator(".f-error")
    expect(error).to_contain_text("non numerici")

    # valid again -> runs successfully
    text_input.fill("5; 10; 15")
    submit(page)
    page.wait_for_timeout(600)
    expect(page.locator("#run-error")).to_be_hidden()


# -- Finding 20 (P1): no Arial/Times anywhere ----------------------------------------------------


@pytest.mark.parametrize("tool_name", ["muro-sostegno", "acciaio-resistenza-incendio"])
def test_no_element_computes_arial_or_times(page: Page, base_url: str, tool_name: str) -> None:
    goto_tool(page, base_url, tool_name)
    load_example(page)
    page.wait_for_timeout(300)

    offenders = page.evaluate(
        """() => {
            const bad = [];
            document.querySelectorAll('body *').forEach((el) => {
                const family = getComputedStyle(el).fontFamily.toLowerCase();
                if (family.includes('arial') || family.includes('times')) {
                    bad.push(el.tagName + '.' + el.className);
                }
            });
            return bad;
        }"""
    )
    assert offenders == [], f"{tool_name}: elements computing Arial/Times: {offenders[:10]}"


# -- Finding 21 (P1): units/details formatted (superscript, decimal comma, <= >=) ---------------


def test_units_and_details_are_formatted(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "ca-trave-rettangolare")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")

    ascii_units = page.evaluate(
        """() => Array.from(document.querySelectorAll('.r-cell-unit, .r-si-figure-unit'))
            .map(el => el.textContent)
            .filter(t => /[a-zA-Z](2|3|4)(?![a-zA-Z0-9])/.test(t))"""
    )
    assert not ascii_units, f"unit text with a raw ASCII exponent (expected a superscript): {ascii_units}"

    details = page.locator(".r-check-detail").all_inner_texts()
    joined = " ".join(details)
    assert ">=" not in joined and "<=" not in joined, f"raw >=/<= leaked into check detail text: {details}"
    assert "≥" in joined or "≤" in joined, "expected at least one ≥/≤ in ca-trave-rettangolare's own check details"
    assert "_" not in joined, f"raw underscore leaked into check detail text: {details}"


# -- Finding 22 (P1): collapsed accordion toggle target height ----------------------------------


def test_dati_section_toggle_is_compact(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    page.wait_for_timeout(300)
    height = page.locator("#form-root .f-section-toggle").first.evaluate("el => el.getBoundingClientRect().height")
    assert height <= 44 + 0.5, f"section toggle taller than 44px: {height}"


# -- Orchestrator: "Espandi tutto / Comprimi tutto" compact, on one line ------------------------


def test_expand_collapse_all_are_compact_text_buttons_on_one_line(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    page.wait_for_timeout(300)

    espandi = page.get_by_role("button", name="Espandi tutto").first
    comprimi = page.get_by_role("button", name="Comprimi tutto").first
    espandi_box = espandi.bounding_box()
    comprimi_box = comprimi.bounding_box()
    assert espandi_box and comprimi_box
    assert abs(espandi_box["y"] - comprimi_box["y"]) < 2, "Espandi/Comprimi tutto must sit on one row"
    assert espandi_box["height"] <= 34, f"expected a compact control height, got {espandi_box['height']}"

    border = espandi.evaluate("el => getComputedStyle(el).borderStyle")
    assert border in ("none", ""), f"expected a plain text button (no border), got border-style: {border!r}"


# -- Orchestrator: sigla badge sits in the corner, not over the pictogram -----------------------


def test_rail_sigla_badge_does_not_cover_the_pictogram(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    page.wait_for_timeout(300)
    if "rail-collapsed" not in (page.evaluate("document.getElementById('app').className") or ""):
        page.locator(".rail-toggle").click()
        page.wait_for_timeout(300)

    overlap = page.evaluate(
        """() => {
            const btn = document.querySelector('.rail-item--active-category');
            const icon = btn ? btn.querySelector('.sm-icon') : null;
            const badge = btn ? btn.querySelector('.rail-sigla-badge') : null;
            if (!icon || !badge) return null;
            const ir = icon.getBoundingClientRect();
            const br = badge.getBoundingClientRect();
            const ox = Math.max(0, Math.min(ir.right, br.right) - Math.max(ir.left, br.left));
            const oy = Math.max(0, Math.min(ir.bottom, br.bottom) - Math.max(ir.top, br.top));
            return (ox * oy) / (ir.width * ir.height);
        }"""
    )
    assert overlap is not None, "expected an active-category rail button with a sigla badge"
    assert overlap < 0.2, f"sigla badge covers {overlap:.0%} of the pictogram, expected a corner touch only"


# -- Orchestrator: empty-Sintesi rule ------------------------------------------------------------


def test_empty_sintesi_shows_chart_when_tool_has_one(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "sisma-spettro")
    load_example(page)
    page.wait_for_timeout(600)

    info = page.evaluate(
        """() => {
            const s = document.getElementById('sintesi');
            return {
                hasVerdict: !!s.querySelector('.r-si-verdict'),
                hasChart: !!s.querySelector('.r-chart svg'),
                hasEmptyMsg: !!s.querySelector('.r-si-empty'),
            };
        }"""
    )
    assert not info["hasVerdict"], "sisma-spettro has no checks; expected no verdict line"
    assert info["hasChart"], "expected the Sintesi's empty-block fallback to show sisma-spettro's chart"
    assert not info["hasEmptyMsg"], "a tool with a chart must show the chart, not the 'Calcolo eseguito' fallback"


def test_empty_sintesi_falls_back_to_one_liner_without_a_chart(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "sisma-vita-riferimento")
    load_example(page)
    page.wait_for_timeout(600)

    info = page.evaluate(
        """() => {
            const s = document.getElementById('sintesi');
            return {
                hasVerdict: !!s.querySelector('.r-si-verdict'),
                hasHighlights: !!s.querySelector('.r-si-figures'),
                hasChart: !!s.querySelector('.r-chart svg'),
                emptyText: s.querySelector('.r-si-empty') ? s.querySelector('.r-si-empty').textContent : null,
            };
        }"""
    )
    if info["hasVerdict"] or info["hasHighlights"] or info["hasChart"]:
        pytest.skip("acciaio-proprieta-temperatura's example now has checks/highlights/a chart -- not the empty case")
    assert info["emptyText"] == "Calcolo eseguito", f"expected the one-line fallback, got {info}"


# -- Orchestrator: rail flyout spans header-bottom to window-bottom -----------------------------


def test_rail_flyout_spans_header_bottom_to_window_bottom(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    page.wait_for_timeout(300)
    if "rail-collapsed" not in (page.evaluate("document.getElementById('app').className") or ""):
        page.locator(".rail-toggle").click()
        page.wait_for_timeout(300)

    page.get_by_role("button", name="Fondazioni", exact=False).first.click()
    flyout = page.locator(".rail-flyout")
    expect(flyout).to_be_visible()
    box = flyout.bounding_box()
    header_bottom = page.locator(".app-header").evaluate("el => el.getBoundingClientRect().bottom")
    viewport_height = page.evaluate("window.innerHeight")
    assert box is not None
    assert abs(box["y"] - header_bottom) < 2, f"flyout must start at the header's own bottom edge: {box['y']} vs {header_bottom}"
    assert abs((box["y"] + box["height"]) - viewport_height) < 2, "flyout must reach the window's own bottom edge"


# -- P0 acceptance: vertical dimension text never intersects the solid it measures --------------


@pytest.mark.parametrize("tool_name", ["fond-plinto-isolato", "fond-trave-collegamento", "neve-accumulo", "muro-sostegno"])
def test_vertical_dimension_text_clears_solid_shapes(page: Page, base_url: str, tool_name: str) -> None:
    goto_tool(page, base_url, tool_name)
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")
    page.wait_for_timeout(200)

    result = page.evaluate(
        """() => {
            const SOLID = ['sk-calcestruzzo', 'sk-terreno', 'sk-acciaio', 'sk-armatura', 'sk-palo'];
            const out = [];
            document.querySelectorAll('.r-si-sketch svg .sk-quota').forEach((g) => {
                const text = g.querySelector('.sk-quota-text text');
                const extLines = g.querySelectorAll('.sk-quota-ext');
                if (!text || extLines.length < 2) return;
                const dy = Math.abs(extLines[0].getBoundingClientRect().top - extLines[1].getBoundingClientRect().top);
                const dx = Math.abs(extLines[0].getBoundingClientRect().left - extLines[1].getBoundingClientRect().left);
                if (dy <= dx) return; // horizontal-ish quota, not this check
                const tr = text.getBoundingClientRect();
                const svg = g.closest('svg');
                svg.querySelectorAll(SOLID.map((c) => '.' + c).join(',')).forEach((solid) => {
                    if (solid.closest('.sk-quota')) return;
                    const sr = solid.getBoundingClientRect();
                    if (sr.width === 0 || sr.height === 0) return;
                    const overlapX = Math.max(0, Math.min(tr.right, sr.right) - Math.max(tr.left, sr.left));
                    const overlapY = Math.max(0, Math.min(tr.bottom, sr.bottom) - Math.max(tr.top, sr.top));
                    if (overlapX > 1 && overlapY > 1) out.push({overlapX, overlapY});
                });
            });
            return out;
        }"""
    )
    assert result == [], f"{tool_name}: a vertical dimension's text overlaps a solid shape: {result}"
