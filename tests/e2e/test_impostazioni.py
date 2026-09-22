"""E2E coverage for WORKBENCH_SPEC §26.8: the `#/impostazioni` office-settings page. Uses the
`isolated_page`/`isolated_base_url` fixtures (tests/e2e/conftest.py) -- a fresh, in-memory
settings store per test, so factory-value assertions never race a PUT from another test in the
same session.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _goto_impostazioni(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/#/impostazioni")
    page.get_by_role("heading", name="Impostazioni").wait_for(state="visible")


def test_reachable_from_rail_and_shows_factory_values(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/#/")
    page.get_by_role("button", name="Impostazioni").click()
    page.get_by_role("heading", name="Impostazioni").wait_for(state="visible")
    expect(page.locator("#im-obiettivo")).to_have_value("1")
    expect(page.locator("#im-minimo")).not_to_be_checked()
    expect(page.get_by_text("Valori di fabbrica, mai modificati")).to_be_visible()


def test_reachable_with_shortcut_g_i(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/#/")
    # Readiness signal: js/main.js only calls `initShortcuts` after the rail has rendered.
    page.get_by_role("button", name="Impostazioni").wait_for(state="visible")
    page.keyboard.press("g")
    page.keyboard.press("i")
    page.get_by_role("heading", name="Impostazioni").wait_for(state="visible")


def test_save_then_reload_shows_new_revision(isolated_page: Page, isolated_base_url: str) -> None:
    page = isolated_page
    _goto_impostazioni(page, isolated_base_url)

    page.locator("#im-obiettivo").fill("0,9")
    page.locator("#im-sigla").fill("AB")
    page.get_by_role("button", name="Salva", exact=True).click()
    page.locator(".im-revisione").filter(has_text="Revisione 1").wait_for(state="visible")

    page.reload()
    page.get_by_role("heading", name="Impostazioni").wait_for(state="visible")
    expect(page.locator("#im-obiettivo")).to_have_value("0,9")
    expect(page.locator(".im-revisione").filter(has_text="Revisione 1")).to_be_visible()


def test_ripristina_predefiniti_then_salva_resets_values(isolated_page: Page, isolated_base_url: str) -> None:
    page = isolated_page
    _goto_impostazioni(page, isolated_base_url)
    page.locator("#im-obiettivo").fill("0,8")
    page.locator("#im-sigla").fill("AB")
    page.get_by_role("button", name="Salva", exact=True).click()
    page.locator(".im-revisione").filter(has_text="Revisione 1").wait_for(state="visible")

    page.get_by_role("button", name="Ripristina predefiniti").click()
    page.get_by_role("button", name="Ripristina", exact=True).click()
    expect(page.locator("#im-obiettivo")).to_have_value("1")
    page.locator("#im-sigla").fill("AB")
    page.get_by_role("button", name="Salva", exact=True).click()
    page.locator(".im-revisione").filter(has_text="Revisione 2").wait_for(state="visible")


def test_invalid_obiettivo_shows_message_next_to_field_and_in_summary(isolated_page: Page, isolated_base_url: str) -> None:
    page = isolated_page
    _goto_impostazioni(page, isolated_base_url)
    page.locator("#im-obiettivo").fill("1,5")
    page.locator("#im-sigla").fill("AB")
    page.get_by_role("button", name="Salva", exact=True).click()
    expect(page.locator(".im-summary")).to_be_visible()


def test_mobile_layout_reaches_page(isolated_mobile_page: Page, isolated_base_url: str) -> None:
    _goto_impostazioni(isolated_mobile_page, isolated_base_url)
    expect(isolated_mobile_page.locator("#im-obiettivo")).to_be_visible()


def test_typing_the_obiettivo_character_by_character_keeps_focus(isolated_page: Page, isolated_base_url: str) -> None:
    """§26.8: `renderSections()` used to rebuild every control (and lose focus/caret) on the FIRST
    keystroke of a text field -- `.fill()` above never catches this (one "input" event for the
    whole value); real keystrokes do."""
    page = isolated_page
    _goto_impostazioni(page, isolated_base_url)
    field = page.locator("#im-obiettivo")
    field.fill("")
    field.click()
    page.keyboard.type("0,90")
    expect(field).to_have_value("0,90")
    assert page.evaluate("document.activeElement.id") == "im-obiettivo"


def test_aggiungi_eccezione_focuses_the_new_row_strumento_select(isolated_page: Page, isolated_base_url: str) -> None:
    page = isolated_page
    _goto_impostazioni(page, isolated_base_url)
    page.get_by_role("button", name="+ Aggiungi eccezione", exact=True).click()
    focused = page.evaluate("document.activeElement.tagName")
    assert focused == "SELECT"
    assert page.evaluate("document.activeElement.getAttribute('aria-label')") == "Strumento"
