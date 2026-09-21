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
    # WORKBENCH_SPEC §3: the Dati column is an accordion with only the first section open by
    # default. The pre-Workbench suite was written against a flat form where every field was
    # always visible; expanding every section here keeps that assumption true for tests whose
    # own intent (validation, persistence, keyboard flow, ...) has nothing to do with the
    # accordion itself, without touching each test's field-filling logic individually.
    # Scoped to `#form-root`: the results sheet (WORKBENCH_SPEC §4) has its OWN "Espandi tutto"
    # in its toolbar once a previous run left groups on the page, and an unscoped locator is
    # ambiguous whenever this navigates from one already-run tool to the next.
    page.locator("#form-root").get_by_role("button", name="Espandi tutto").click()


def expand_all_results(page: Page) -> None:
    """Opens every collapsed result group (WORKBENCH_SPEC §4: only "Verifiche" and groups with a
    failed check open by default; everything else, incl. row tables/charts, starts closed).
    Relies on Playwright's own actionability retry (NOT `Locator.count()`, which resolves
    immediately with no wait) since the toolbar only exists once the run that produced groups has
    actually finished rendering, which can still be in flight right after `submit()` returns."""
    page.locator("#results-root").get_by_role("button", name="Espandi tutto").first.click()


def load_example(page: Page) -> None:
    page.get_by_role("button", name=CARICA_ESEMPIO).click()


def submit(page: Page) -> None:
    """Runs the current tool. WORKBENCH_SPEC §3: "Calcola" only renders while live calculation
    is off (a big table, a slow tool, or the header switch); when it is on (the default) the
    equivalent explicit-run gesture is Ctrl+Enter, which WORKBENCH_SPEC §2 guarantees works from
    anywhere, live on or off."""
    button = page.get_by_role("button", name=CALCOLA)
    if button.count() > 0 and button.first.is_visible():
        button.first.click()
    else:
        page.keyboard.press("Control+Enter")


def field_id(name: str) -> str:
    return f"#field-{name}"


def field_error_id(name: str) -> str:
    return f"#field-{name}-error"


def tab_to_run(page: Page, max_tabs: int = 80) -> list[str]:
    """Tab from `#tool-title` all the way to "Carica esempio" (in `#form-actions`, after every
    field/section-toggle in DOM order) and activate it with Enter -- a fully keyboard-only way to
    both fill the required fields and run the tool: forms.js's example button always calls
    `requestRun(..., "example")`, live on or off, and WORKBENCH_SPEC §2's focus-after-run applies
    to that reason too. WORKBENCH_SPEC §6 dropped `#tool-search` (Home + the palette replace it),
    so the walk starts at `#tool-title` instead. Returns the outline-width seen at every stop, for
    the keyboard-focus-visibility assertion."""
    # `Locator.focus()` only waits for the element to be attached, not visible/populated, and
    # `#tool-title` is static markup that exists before `fetchSchema()` resolves -- without this
    # wait the walk could start (and start counting tab stops) before forms.js has built a single
    # field, undercounting the real path to "Carica esempio" and failing on a fast run.
    page.locator("#form-root .f-section-toggle, #form-root .f-field").first.wait_for(state="visible")
    page.locator("#tool-title").focus()
    outlines: list[str] = []
    for _ in range(max_tabs):
        page.keyboard.press("Tab")
        outlines.append(
            page.evaluate("getComputedStyle(document.activeElement).outlineWidth")
        )
        tag = page.evaluate("document.activeElement.tagName")
        text = page.evaluate("document.activeElement.textContent || ''")
        if tag == "BUTTON" and CARICA_ESEMPIO in text:
            page.keyboard.press("Enter")
            return outlines
    raise AssertionError(f"Tab never reached {CARICA_ESEMPIO!r} within {max_tabs} presses")
