"""E2E coverage for the UI-polish review findings (chart legend colour, direct-label collision,
narrow-viewport chart legibility, condensed row-table headers)."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import expand_all_results, goto_tool, load_example, submit

pytestmark = pytest.mark.e2e


def test_legend_text_uses_ink_not_series_colour(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "sisma-spettro")
    load_example(page)
    submit(page)
    # "Carica esempio" already ran the tool once; `submit()` (Ctrl+Enter, live is on for this
    # tool) queues a SECOND run right behind it (live.js "one request in flight" rule) -- wait for
    # the chart's own series paths, not just the legend <li> count, so the colour reads below land
    # on the settled SECOND render rather than catching the chart mid-rebuild.
    expect(page.locator("svg path[data-series]")).to_have_count(2)

    legend_items = page.locator(".c-legend li")
    expect(legend_items).to_have_count(2)
    label_colors = [
        legend_items.nth(i).locator(".c-legend-label").evaluate("el => getComputedStyle(el).color")
        for i in range(2)
    ]
    assert label_colors[0] == label_colors[1], f"legend labels must share one text colour: {label_colors}"

    swatch_colors = [
        legend_items.nth(i).locator(".c-legend-swatch").evaluate(
            "el => getComputedStyle(el).backgroundColor || getComputedStyle(el).borderTopColor"
        )
        for i in range(2)
    ]
    assert swatch_colors[0] != swatch_colors[1], "the two series swatches must stay visually distinct"
    assert label_colors[0] not in swatch_colors, "legend text must not be painted in a series colour"


def test_direct_labels_use_symbol_tspans_and_hide_when_close(page: Page, base_url: str) -> None:
    # Exercise chart.js directly (real ES module import in the page) so the collision rule is
    # verified against controlled endpoints instead of hoping a real dataset converges.
    goto_tool(page, base_url, "sisma-spettro")

    far = page.evaluate(
        """async () => {
            const { renderChart } = await import('/js/chart.js');
            const host = document.createElement('div');
            document.body.append(host);
            const series = [
                { key: 'a', label: 'Serie A', symbol: 'S_e(T)', className: 'c-series-1' },
                { key: 'b', label: 'Serie B', symbol: 'S_d(T)', className: 'c-series-2' },
            ];
            renderChart(host, {
                rows: [ { x: 0, a: 0, b: 0 }, { x: 1, a: 10, b: 0 } ],
                chart: { x: 'x', y: ['a', 'b'], x_label: 'x', y_label: 'y' },
                series,
            });
            const texts = Array.from(host.querySelectorAll('svg g.c-series-1 text, svg g.c-series-2 text'));
            return {
                count: texts.length,
                hasTspanSub: texts.some(t => t.querySelector('tspan[baseline-shift="sub"]')),
                rawKeyLeaked: texts.some(t => (t.textContent || '').includes('S_e') || (t.textContent || '').includes('S_d')),
            };
        }"""
    )
    assert far["count"] == 2, "far-apart endpoints must each get a direct label"
    assert far["hasTspanSub"], "direct label must render a real <tspan> subscript, not plain text"
    assert not far["rawKeyLeaked"], "direct label must use the symbol, never the raw '_'-joined field key"

    close = page.evaluate(
        """async () => {
            const { renderChart } = await import('/js/chart.js');
            const host = document.createElement('div');
            document.body.append(host);
            const series = [
                { key: 'a', label: 'Serie A', symbol: 'S_e(T)', className: 'c-series-1' },
                { key: 'b', label: 'Serie B', symbol: 'S_d(T)', className: 'c-series-2' },
            ];
            renderChart(host, {
                rows: [ { x: 0, a: 0, b: 0 }, { x: 1, a: 1, b: 1.001 } ],
                chart: { x: 'x', y: ['a', 'b'], x_label: 'x', y_label: 'y' },
                series,
            });
            const texts = host.querySelectorAll('svg g.c-series-1 text, svg g.c-series-2 text');
            const legend = host.querySelectorAll('.c-legend li');
            return { textCount: texts.length, legendCount: legend.length };
        }"""
    )
    assert close["textCount"] == 0, "converging endpoints must not draw overlapping direct labels"
    assert close["legendCount"] == 2, "the legend must still be present as the fallback"


def test_narrow_chart_min_height_and_tick_font_size(mobile_page, base_url: str) -> None:
    page, _ = mobile_page
    goto_tool(page, base_url, "sisma-spettro")
    load_example(page)
    submit(page)
    # WORKBENCH_SPEC §4: the row-table/chart group starts closed (only "Verifiche" opens by
    # default), so the chart isn't visible -- and its box has no real height -- until expanded.
    expand_all_results(page)

    svg = page.locator(".c-svg").first
    expect(svg).to_be_visible()
    box = svg.bounding_box()
    assert box and box["height"] >= 200, f"expected a >=200px plot on narrow viewports, got {box}"

    tick_font_px = page.evaluate(
        """() => {
            const text = document.querySelector('.c-axis text');
            return text ? parseFloat(getComputedStyle(text).fontSize) : 0;
        }"""
    )
    assert tick_font_px >= 11, f"expected axis tick labels >=11px on narrow viewports, got {tick_font_px}"


def test_row_table_header_is_symbol_plus_unit_with_legend_line(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "sisma-spettro")
    load_example(page)
    submit(page)

    header_cells = page.locator(".r-table thead th")
    expect(header_cells).to_have_count(3)
    t_header = header_cells.nth(0)
    long_description = t_header.get_attribute("title")
    assert long_description, "expected the full description as the header's title tooltip"
    header_text = t_header.inner_text()
    assert header_text != long_description, "header text must be the symbol, not the full description"
    assert len(header_text) < len(long_description), "condensed header must be shorter than the description"

    legend_line = page.locator(".r-table caption .r-table-legend")
    expect(legend_line).to_have_count(1)
    legend_text = legend_line.inner_text()
    assert long_description in legend_text, "the full description must appear once, in the Legenda line"
