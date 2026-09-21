"""Shared page actions built only on the fixed ids/classes/data attributes of DESIGN_SPEC §5."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

CALCOLA = "Calcola"
CARICA_ESEMPIO = "Carica esempio"


def goto_tool(page: Page, base_url: str, tool_name: str) -> None:
    page.goto(f"{base_url}/#/{tool_name}")
    page.locator("#tool-title").wait_for(state="visible")


def load_example(page: Page) -> None:
    page.get_by_role("button", name=CARICA_ESEMPIO).click()


def submit(page: Page) -> None:
    page.get_by_role("button", name=CALCOLA).click()


def field_id(name: str) -> str:
    return f"#field-{name}"


def field_error_id(name: str) -> str:
    return f"#field-{name}-error"


def tab_to_calcola(page: Page, max_tabs: int = 60) -> list[str]:
    """Tab from `#tool-search` to the Calcola button, activating "Carica esempio" along the
    way (it sits earlier in tab order, per forms.js) so the required fields are filled by the
    time Calcola is reached. Returns the outline-width seen at each stop."""
    page.locator("#tool-search").click()
    outlines: list[str] = []
    for _ in range(max_tabs):
        page.keyboard.press("Tab")
        outlines.append(
            page.evaluate("getComputedStyle(document.activeElement).outlineWidth")
        )
        is_button = page.evaluate("document.activeElement.tagName") == "BUTTON"
        text = page.evaluate("document.activeElement.textContent || ''")
        if is_button and CARICA_ESEMPIO in text:
            page.keyboard.press("Enter")
        elif is_button and CALCOLA in text:
            return outlines
    raise AssertionError(f"Tab never reached the {CALCOLA!r} button within {max_tabs} presses")
