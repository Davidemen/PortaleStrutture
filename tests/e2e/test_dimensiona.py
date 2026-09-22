"""E2E coverage for WORKBENCH_SPEC §23: the "Dimensiona" dialog. `ca-taglio-non-armato`'s example
(h_mm=500) is used rather than the golden `muro-sostegno` case (tests/shared/dimensiona/) -- the
UI only needs a fast, real search to exercise the flow end to end, not the specific outcome.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool, load_example

pytestmark = pytest.mark.e2e

TOOL = "ca-taglio-non-armato"
SEARCH_TIMEOUT_MS = 15_000


def _open_dimensiona(page: Page) -> None:
    page.get_by_role("button", name="⌖ Dimensiona…", exact=True).click()
    page.locator(".dm-panel").wait_for(state="visible")


def _open_tool(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, TOOL)
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")


def test_cerca_disabled_until_passo_filled(page: Page, base_url: str) -> None:
    _open_tool(page, base_url)
    _open_dimensiona(page)

    cerca = page.locator(".dm-panel").get_by_role("button", name="Cerca", exact=True)
    expect(cerca).to_have_attribute("aria-disabled", "true")
    reason = page.locator("#dm-cerca-reason")
    expect(reason).to_be_visible()

    page.locator("#dm-da").fill("250")
    page.locator("#dm-a").fill("1000")
    page.locator("#dm-passo").fill("10")
    expect(cerca).to_have_attribute("aria-disabled", "false")
    expect(reason).to_be_hidden()


def test_obiettivo_edited_by_hand_survives_campo_change_and_blocks_search_when_invalid(
    page: Page, base_url: str
) -> None:
    """§23.1: an obiettivo typed by the engineer is never rewritten by the settings fetch, and
    the search must not start without a valid one (no silent default to 1,00)."""
    _open_tool(page, base_url)
    _open_dimensiona(page)

    obiettivo = page.locator("#dm-obiettivo")
    cerca = page.locator(".dm-panel").get_by_role("button", name="Cerca", exact=True)
    reason = page.locator("#dm-cerca-reason")

    obiettivo.fill("0,85")
    page.locator("#dm-da").fill("250")
    page.locator("#dm-a").fill("1000")
    page.locator("#dm-passo").fill("10")
    expect(cerca).to_have_attribute("aria-disabled", "false")
    expect(obiettivo).to_have_value("0,85")

    obiettivo.fill("")
    expect(cerca).to_have_attribute("aria-disabled", "true")
    expect(reason).to_be_visible()
    expect(reason).to_have_text("Indicare un obiettivo di sfruttamento fra 0 e 1.")


def test_search_shows_reliability_and_applica_updates_field(page: Page, base_url: str) -> None:
    _open_tool(page, base_url)
    _open_dimensiona(page)

    page.locator("#dm-campo").select_option("h_mm")
    page.locator("#dm-da").fill("250")
    page.locator("#dm-a").fill("1000")
    page.locator("#dm-passo").fill("10")
    page.locator(".dm-panel").get_by_role("button", name="Cerca", exact=True).click()

    page.locator(".dm-esito").wait_for(state="visible", timeout=SEARCH_TIMEOUT_MS)
    expect(page.locator(".dm-affidabile")).to_be_visible()

    applica = page.get_by_role("button", name="Applica")
    if applica.count() > 0:
        applica.click()
        expect(page.locator("#field-h_mm")).not_to_have_value("500")


def test_focus_then_shortcut_preselects_field_and_escape_closes(page: Page, base_url: str) -> None:
    _open_tool(page, base_url)
    page.locator("#field-h_mm").click()
    # Blur the field before the shortcut -- "g"/"d" typed while an editable control has focus
    # must land in the field, not trigger the global shortcut (WORKBENCH_SPEC #6).
    page.locator("#tool-title").click()
    page.keyboard.press("g")
    page.keyboard.press("d")
    page.locator(".dm-panel").wait_for(state="visible")
    expect(page.locator("#dm-campo")).to_have_value("h_mm")

    page.keyboard.press("Escape")
    expect(page.locator(".dm-panel")).to_have_count(0)


def test_ctrl_enter_in_dialog_does_not_also_trigger_global_calcola(page: Page, base_url: str) -> None:
    _open_tool(page, base_url)
    _open_dimensiona(page)
    page.locator("#dm-da").fill("250")
    page.locator("#dm-a").fill("1000")
    page.locator("#dm-passo").fill("10")
    page.locator("#dm-passo").press("Control+Enter")
    # Still on the dialog: the global "Calcola" shortcut did not steal the keystroke and close it.
    expect(page.locator(".dm-panel")).to_be_visible()
    page.locator(".dm-esito").wait_for(state="visible", timeout=SEARCH_TIMEOUT_MS)


def test_mobile_layout_reaches_dialog(mobile_page: tuple[Page, object], base_url: str) -> None:
    page, _ = mobile_page
    _open_tool(page, base_url)
    _open_dimensiona(page)
    expect(page.locator(".dm-panel")).to_be_visible()
