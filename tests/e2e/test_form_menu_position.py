"""The Dati action bar's "⋯" menu (js/forms.js `buildMenu`) must stay inside the Dati column.
With a saved element the bar shows "Salvato: … / Salva / Salva come nuovo" too, so in a narrow
column the "⋯" button wraps to the LEFT edge -- a menu anchored `right: 0` then opened under the
sidebar (seen by the owner as an empty white box). The menu flips to open rightwards there."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool, load_example
from .test_progetti import save_current_tool_as_new_element

pytestmark = pytest.mark.e2e


def _box(page: Page, selector: str) -> dict[str, float]:
    box = page.locator(selector).bounding_box()
    assert box is not None, selector
    return box


def test_overflow_menu_stays_inside_the_dati_column_when_the_bar_wraps(page: Page, base_url: str) -> None:
    page.set_viewport_size({"width": 1000, "height": 800})
    response = page.request.post(f"{base_url}/api/progetti", data={"codice": "MENU", "nome": "Progetto menu", "committente": "", "note": ""})
    progetto_id = response.json()["id"]
    goto_tool(page, base_url, "neve-carico-falda")
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome="Neve menu")
    expect(page.get_by_role("button", name="Salva", exact=True)).to_be_visible()

    page.locator(".f-menu-btn").click()
    menu = page.locator(".f-menu-list")
    expect(menu).to_be_visible()
    # The flip happens in the <details> `toggle` handler, which the browser fires asynchronously
    # after the click: `ratio=1` keeps retrying until the first item is FULLY on screen.
    expect(menu.locator(".f-menu-item").first).to_be_in_viewport(ratio=1)
    column = _box(page, "#form-actions")
    box = _box(page, ".f-menu-list")
    assert box["x"] >= column["x"], f"menu opens under the sidebar: menu x={box['x']}, column x={column['x']}"
    assert box["x"] + box["width"] <= 1000
