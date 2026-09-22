"""The rail's expand/collapse button must be on screen WITHOUT scrolling the tool list (owner's
finding, 2026-09-22: "it should be possible to collapse the navbar" -- the button existed but sat
at the end of a 1100px-tall scrolling rail, below the fold on a 900px screen). The list scrolls
on its own; the toggle is a fixed footer of the rail."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool

pytestmark = pytest.mark.e2e


def test_rail_toggle_is_on_screen_while_the_list_scrolls(page: Page, base_url: str) -> None:
    page.set_viewport_size({"width": 1400, "height": 700})
    goto_tool(page, base_url, "vento-cpe-rettangolare")
    # Root cause of the hidden button: `--head-h` (tokens.css) was 23px shorter than the real
    # header, so every column overflowed the viewport by that much and the page itself scrolled.
    assert page.evaluate("document.documentElement.scrollHeight") == 700
    toggle = page.locator("#tool-index .rail-toggle")
    expect(toggle).to_be_in_viewport(ratio=1)
    box = toggle.bounding_box()
    assert box is not None and box["y"] + box["height"] <= 700
    scrolls = page.locator("#tool-index .rail-list").evaluate("el => el.scrollHeight > el.clientHeight && getComputedStyle(el).overflowY === 'auto'")
    assert scrolls, "the tool list itself must be the scrolling region"

    toggle.click()  # collapse: still on screen in the 56px activity bar
    expect(page.locator("#tool-index .rail-toggle")).to_be_in_viewport(ratio=1)
    page.locator("#tool-index .rail-toggle").click()  # and back
    expect(page.locator("#tool-index .rail-toggle")).to_have_attribute("aria-label", "Comprimi la barra di navigazione")
