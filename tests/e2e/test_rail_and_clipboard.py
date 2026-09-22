"""E2E coverage for WORKBENCH_SPEC.md §12 (the redesigned navigation rail: a 10-destination
activity bar + flyouts when collapsed, accordions when expanded) and the clipboard bug fix
(js/clipboard.js): "Copia link" / click-to-copy / "Copia tabella" must never claim "Copiato" when
nothing was actually copied, over a plain-http, non-secure-context VPN connection where
`navigator.clipboard` is undefined.
"""
from __future__ import annotations

import re

import pytest
from playwright.sync_api import Locator, Page, expect

from ._actions import field_id, goto_tool, load_example

pytestmark = pytest.mark.e2e

RAIL_DESTINATIONS = [
    "Home", "Cerca", "Preferiti", "Recenti", "Registro correzioni", "Progetti",
    "Carichi", "Calcestruzzo armato", "Acciaio", "Geotecnica", "Fondazioni",
]
# Home, Cerca, Preferiti, Recenti, Registro correzioni, Progetti (WORKBENCH_SPEC §13.1/§14.1)
FIXED_DESTINATIONS = 6


def _class_regex(fragment: str) -> re.Pattern[str]:
    """A whole-token match for one CSS class among possibly several on the same attribute."""
    return re.compile(rf"(^|\s){re.escape(fragment)}(\s|$)")

# Init script used to simulate the VPN's non-secure-context origin (http://<ip>:<port>), where
# `navigator.clipboard` is undefined -- overriding the PROTOTYPE getter (not just the own
# property) so every subsequent read of `navigator.clipboard`, anywhere in the app, sees it.
NO_CLIPBOARD_API_SCRIPT = "Object.defineProperty(Navigator.prototype, 'clipboard', { get: () => undefined, configurable: true });"
# On top of the above: also break the execCommand("copy") fallback, so NEITHER copy path can
# succeed -- the only way to reach the "manual copy field, never Copiato" branch.
FORCE_TOTAL_FAILURE_SCRIPT = NO_CLIPBOARD_API_SCRIPT + " document.execCommand = () => false;"


def _open_menu_and_click_copy_link(page: Page) -> Locator:
    page.get_by_label("Altre azioni").click()
    button = page.locator(".f-menu-list .f-menu-item").first
    button.click()
    return button


# -- rail: collapsed activity bar -------------------------------------------------------------


def _category_names(page: Page) -> list[str]:
    """The distinct top-level `Tool.group` values the backend currently serves, in first-seen
    order. The e2e test server (tests/e2e/_demo_tool.py) registers 3 extra fixture tools under an
    extra "Demo" category on top of the 5 real ones the WORKBENCH_SPEC table names -- the rail is
    schema-driven (group-driven), so a real 6th category legitimately adds a 6th destination
    button; these helpers assert "the 5 named categories are present, in order" rather than
    hard-coding a production-only destination count."""
    tools = page.evaluate("() => fetch('/api/tools').then(r => r.json())")
    seen: list[str] = []
    for tool in tools:
        level1 = (tool["group"] or "Strumenti").split(" / ")[0]
        if level1 not in seen:
            seen.append(level1)
    return seen


def test_collapsed_rail_has_ten_destinations_and_toggle(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC #12/#13.1/#14.1: collapsed = Home, Cerca, Preferiti, Recenti, Registro
    correzioni, Progetti + one destination per top-level category (exactly the five named ones on
    the production registry) + the expand/collapse toggle -- no individual tools."""
    goto_tool(page, base_url, "muro-sostegno")
    page.locator(".rail-toggle").click()  # force collapsed at >=1100px
    categories = _category_names(page)
    items = page.locator("#tool-index .rail-list > .rail-item")
    expect(items).to_have_count(FIXED_DESTINATIONS + len(categories))
    names = items.evaluate_all("els => els.map(e => e.querySelector('.rail-label').textContent)")
    assert names[:FIXED_DESTINATIONS] == RAIL_DESTINATIONS[:FIXED_DESTINATIONS], (
        f"unexpected/out-of-order fixed destinations: {names[:FIXED_DESTINATIONS]}"
    )
    assert names[FIXED_DESTINATIONS:FIXED_DESTINATIONS + 5] == RAIL_DESTINATIONS[FIXED_DESTINATIONS:], (
        f"the five named categories must come first, in order: {names[FIXED_DESTINATIONS:]}"
    )
    assert page.locator("#tool-index .rail-toggle").count() == 1
    # no individual tool row exists outside an opened flyout
    assert page.locator("#tool-index .rail-list .rail-row").count() == 0


def test_all_icon_path_data_are_distinct(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC #12: "every icon's path data differs" -- js/icons.js path data for every
    destination pictogram actually used in the rail."""
    goto_tool(page, base_url, "muro-sostegno")
    paths = page.evaluate(
        """async () => {
          const { buildIcon } = await import('/js/icons.js');
          const keys = ['home', 'cerca', 'preferiti', 'recenti', 'registro', 'progetti', 'carichi', 'calcestruzzo-armato', 'acciaio', 'geotecnica', 'fondazioni'];
          return keys.map(key => {
            const svg = buildIcon(key);
            return [...svg.querySelectorAll('path')].map(p => p.getAttribute('d')).join('|');
          });
        }"""
    )
    assert len(set(paths)) == len(paths), f"two destination icons share identical path data: {paths}"


def test_destinations_have_accessible_name_and_tooltip(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC #12: each of the 10 destinations has an accessible name and a tooltip
    (name + shortcut for Cerca)."""
    goto_tool(page, base_url, "muro-sostegno")
    page.locator(".rail-toggle").click()
    items = page.locator("#tool-index .rail-list > .rail-item")
    for i in range(items.count()):
        item = items.nth(i)
        assert item.get_attribute("title"), f"destination {i} has no tooltip"
        # accessible name = the (visually hidden) .rail-label text content
        assert item.locator(".rail-label").inner_text().strip()
    cerca_title = items.nth(1).get_attribute("title")
    assert "Ctrl K" in cerca_title, f"Cerca tooltip must carry the shortcut, got {cerca_title!r}"


def test_keyboard_flow_enter_downdown_enter_navigates_and_closes(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC #12 acceptance: Tab to a category, Enter opens the flyout with focus on the
    first tool, down-down + Enter navigates and closes it."""
    goto_tool(page, base_url, "muro-sostegno")
    page.locator(".rail-toggle").click()
    fondazioni = page.get_by_role("button", name="Fondazioni")
    fondazioni.focus()  # reached via Tab in real use; focusing directly is the same end state
    page.keyboard.press("Enter")
    first_row = page.locator(".rail-flyout .rail-row-open").first
    expect(first_row).to_be_focused()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    target = page.evaluate("document.activeElement.dataset.tool")
    page.keyboard.press("Enter")
    page.locator("#tool-title").wait_for(state="visible")
    assert page.locator(".rail-flyout").is_hidden(), "the flyout must close after a selection"
    assert f"#/{target}" in page.url, f"expected to navigate to {target}, got {page.url}"


def test_esc_returns_focus_to_trigger(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    page.locator(".rail-toggle").click()
    trigger = page.get_by_role("button", name="Carichi")
    trigger.click()
    expect(page.locator(".rail-flyout")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator(".rail-flyout")).to_be_hidden()
    expect(trigger).to_be_focused()


def test_active_category_marked_with_sigla(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC #12: the active tool's category button is marked and shows the tool's
    sigla, so the collapsed rail always says where you are."""
    goto_tool(page, base_url, "muro-sostegno")  # sigla MUR, group Geotecnica
    page.locator(".rail-toggle").click()
    geotecnica = page.get_by_role("button", name="Geotecnica")
    expect(geotecnica).to_have_class(_class_regex("rail-item--active-category"))
    badge = geotecnica.locator(".rail-sigla-badge")
    expect(badge).to_have_text("MUR")
    other = page.get_by_role("button", name="Fondazioni")
    assert "rail-item--active-category" not in (other.get_attribute("class") or "")


def test_every_tool_reachable_in_two_actions_from_collapsed_rail(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC #12: "every tool is reachable in <=2 actions from the collapsed rail" --
    spot-check one tool per category: 1 click opens the category flyout, 1 click on a row
    navigates."""
    goto_tool(page, base_url, "muro-sostegno")
    page.locator(".rail-toggle").click()
    for category, tool_name in [("Carichi", "sisma-spettro"), ("Acciaio", "acciaio-colonna-h-ec3"), ("Fondazioni", "fond-plinto-isolato")]:
        page.get_by_role("button", name=category, exact=True).click()  # action 1
        page.locator(f'.rail-flyout .rail-row-open[data-tool="{tool_name}"]').click()  # action 2
        page.locator("#tool-title").wait_for(state="visible")
        assert f"#/{tool_name}" in page.url


def test_flyout_opening_does_not_shift_layout(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    page.locator(".rail-toggle").click()
    before = page.locator("#form-pane").bounding_box()
    page.get_by_role("button", name="Fondazioni").click()
    expect(page.locator(".rail-flyout")).to_be_visible()
    after = page.locator("#form-pane").bounding_box()
    assert before == after, f"content shifted when the flyout opened: {before} -> {after}"


def test_rail_targets_are_44px(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    page.locator(".rail-toggle").click()
    heights = page.locator("#tool-index .rail-item, #tool-index .rail-toggle").evaluate_all(
        "els => els.map(e => e.getBoundingClientRect().height)"
    )
    assert heights and all(h >= 44 for h in heights), f"rail targets below 44px: {heights}"
    page.get_by_role("button", name="Fondazioni").click()
    row_heights = page.locator(".rail-flyout .rail-row-open").evaluate_all("els => els.map(e => e.getBoundingClientRect().height)")
    assert row_heights and all(h >= 44 for h in row_heights), f"flyout row targets below 44px: {row_heights}"


def test_forced_collapsed_between_720_and_1099(tablet_page: tuple[Page, object], base_url: str) -> None:
    """WORKBENCH_SPEC #12: "works at 720-1099px where the rail is forced collapsed"."""
    page, _ = tablet_page
    goto_tool(page, base_url, "muro-sostegno")
    items = page.locator("#tool-index .rail-list > .rail-item")
    expect(items).to_have_count(FIXED_DESTINATIONS + len(_category_names(page)))
    assert page.locator("#tool-index .rail-list .rail-row").count() == 0, "still no individual tools, forced-collapsed or not"
    expect(page.locator("#app")).to_have_class(_class_regex("rail-collapsed"))


# -- clipboard: copyText() never lies -----------------------------------------------------------


def test_clipboard_fallback_copies_when_api_missing(page: Page, base_url: str) -> None:
    """Simulates the VPN's insecure-context origin (no `navigator.clipboard`): the off-screen-
    textarea + execCommand fallback must genuinely copy. Verified by reading the REAL (headless-
    Chromium virtual) clipboard back from a SECOND, uninstrumented page in the same context --
    a native Ctrl+V paste into a plain `<input>` is unreliable under headless Chromium (verified
    manually: even a baseline `navigator.clipboard.writeText()` + Ctrl+V does not land, and
    `execCommand('paste')` is disabled by default), so this is the robust equivalent: it proves
    bytes actually reached the browser's clipboard, not just that our own function returned true.
    """
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page.add_init_script(NO_CLIPBOARD_API_SCRIPT)
    goto_tool(page, base_url, "muro-sostegno")
    assert page.evaluate("navigator.clipboard") is None, "test setup: clipboard API must be gone"

    button = _open_menu_and_click_copy_link(page)
    expect(button).to_have_text("Copiato")
    assert page.locator(".sm-clip-fallback").count() == 0, "no manual field when the fallback itself succeeded"

    # A SECOND, uninstrumented page in the SAME context (page.context, not a separate fixture --
    # pytest-playwright's own `context` fixture would build an unrelated default context/profile).
    verify_page = page.context.new_page()
    verify_page.goto(f"{base_url}/#/")
    verify_page.wait_for_timeout(100)
    clipboard_content = verify_page.evaluate("navigator.clipboard.readText()")
    assert "muro-sostegno" in clipboard_content and clipboard_content.startswith(base_url), (
        f"the textarea/execCommand fallback did not really copy the link, got {clipboard_content!r}"
    )
    verify_page.close()


def test_clipboard_forced_failure_shows_manual_field_never_copiato(page: Page, base_url: str) -> None:
    """Both copy paths fail (no `navigator.clipboard`, `execCommand` stubbed to false): the
    button must NEVER show "Copiato", and a labelled, pre-selected, read-only manual-copy field
    with the "Copia non riuscita" hint must appear instead."""
    page.add_init_script(FORCE_TOTAL_FAILURE_SCRIPT)
    goto_tool(page, base_url, "muro-sostegno")

    button = _open_menu_and_click_copy_link(page)
    page.wait_for_timeout(200)
    assert button.evaluate("el => el.textContent") == "Copia link", 'the button must never claim "Copiato" on a real failure'

    fallback = page.locator(".sm-clip-fallback")
    expect(fallback).to_have_count(1)
    expect(fallback.locator(".sm-clip-fallback-label")).to_contain_text("Copia non riuscita")
    value_input = fallback.locator(".sm-clip-fallback-input")
    assert "muro-sostegno" in value_input.input_value()
    assert value_input.evaluate("el => el === document.activeElement"), "the manual field must be focused"
    selected = page.evaluate("() => { const el = document.activeElement; return el.selectionEnd - el.selectionStart; }")
    assert selected == len(value_input.input_value()), "the manual field's text must be pre-selected"


def test_table_result_copy_never_claims_success_on_forced_failure(page: Page, base_url: str) -> None:
    """The same bug existed at the two other call sites (results-toolbar.js click-to-copy,
    table.js "Copia tabella"); spot-check "Copia tabella" on a tool with a row table."""
    page.add_init_script(FORCE_TOTAL_FAILURE_SCRIPT)
    goto_tool(page, base_url, "sisma-spettro")
    load_example(page)
    page.locator("#results-root").get_by_role("button", name="Espandi tutto").first.click()
    copy_btn = page.get_by_role("button", name="Copia tabella")
    copy_btn.click()
    page.wait_for_timeout(200)
    assert copy_btn.evaluate("el => el.textContent") == "Copia tabella", 'must never show "Copiato" on a real failure'
    expect(page.locator(".sm-clip-fallback")).to_have_count(1)


# -- share link round-trip ------------------------------------------------------------------


def test_share_link_round_trip_in_fresh_tab(page: Page, base_url: str) -> None:
    """A share link must restore decimal values, enums, booleans (incl. an Avanzate-only field)
    and a unit-selector tool's own selector in a FRESH tab/context -- and must say so when a
    table is intentionally left out of the link (fond-plinto-isolato has two table inputs)."""
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    goto_tool(page, base_url, "fond-plinto-isolato")
    load_example(page)

    ax_before = page.locator(field_id("ax_m")).input_value()
    classe_before = page.locator(field_id("classe_calcestruzzo")).input_value()
    sistema_before = page.locator(field_id("sistema_unita")).input_value()
    # legacy_compat is under "Avanzate" (a closed <details>, not one of the accordion sections
    # `goto_tool` expands): open it before reading its checkbox state.
    page.locator("#form-root .f-advanced > summary").click()
    legacy_before = page.locator(field_id("legacy_compat")).is_checked()

    button = _open_menu_and_click_copy_link(page)
    expect(button).to_have_text("Copiato")
    expect(page.locator(".sm-clip-note")).to_contain_text("La tabella non è inclusa nel link")
    url = page.evaluate("navigator.clipboard.readText()")
    assert url.startswith(f"{base_url}/#/fond-plinto-isolato?"), f"unexpected link shape: {url!r}"

    fresh = page.context.new_page()
    fresh.goto(url)
    fresh.locator("#tool-title").wait_for(state="visible")
    fresh.locator("#form-root").get_by_role("button", name="Espandi tutto").click()

    assert fresh.locator(field_id("ax_m")).input_value() == ax_before, "decimal value did not round-trip"
    assert fresh.locator(field_id("classe_calcestruzzo")).input_value() == classe_before, "enum value did not round-trip"
    assert fresh.locator(field_id("sistema_unita")).input_value() == sistema_before, "unit selector did not round-trip"
    fresh.locator("#form-root .f-advanced > summary").click()
    assert fresh.locator(field_id("legacy_compat")).is_checked() == legacy_before, "boolean value did not round-trip"
    fresh.close()
