"""Result rows: the symbol must never run over its own description (owner's finding, 2026-09-22:
"c_pe,sopravento" painted across the label on vento-cpe). The symbol column is a fixed grid track
(css/results.css `.r-row`), so a long subscript has to fit or wrap inside it -- checked on the
three tools with the longest symbols in the whole registry (audit of every model's `symbol`)."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page

from ._actions import expand_all_results, goto_tool, load_example

pytestmark = pytest.mark.e2e

_OVERLAPS = """() => {
    const out = [];
    for (const row of document.querySelectorAll('.r-row')) {
        const symbol = row.querySelector('.r-cell-symbol .r-symbol');
        const label = row.querySelector('.r-cell-label');
        if (!symbol || !label || symbol.getClientRects().length === 0) continue;
        const s = symbol.getBoundingClientRect(), l = label.getBoundingClientRect();
        if (s.right > l.left + 0.5) out.push(`${symbol.textContent} (${Math.round(s.right - l.left)}px into the label)`);
    }
    return out;
}"""


@pytest.mark.parametrize("tool", ["vento-cpe-rettangolare", "ca-sle-limitazione-tensioni", "acciaio-colonna-h-ec3"])
def test_symbols_never_overlap_their_description(page: Page, base_url: str, tool: str) -> None:
    goto_tool(page, base_url, tool)
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    expand_all_results(page)
    assert page.locator(".r-row").count() > 0
    assert page.evaluate(_OVERLAPS) == []
