"""E2E coverage for WORKBENCH_SPEC §24: the "Sensibilità" dialog."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool, load_example

pytestmark = pytest.mark.e2e

TOOL = "ca-taglio-non-armato"
CALCOLA_TIMEOUT_MS = 15_000


def _open_tool(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, TOOL)
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")


def _open_sensibilita(page: Page) -> None:
    page.get_by_role("button", name="∿ Sensibilità…", exact=True).click()
    page.locator(".sv-panel").wait_for(state="visible")


def test_chart_and_table_appear_with_target_line(page: Page, base_url: str) -> None:
    _open_tool(page, base_url)
    _open_sensibilita(page)

    page.locator("#sv-campo").select_option("h_mm")
    page.locator("#sv-da").fill("250")
    page.locator("#sv-a").fill("1000")
    page.locator("#sv-punti").fill("11")
    page.get_by_role("button", name="Calcola", exact=True).click()

    page.locator(".sv-chart svg").wait_for(state="visible", timeout=CALCOLA_TIMEOUT_MS)
    expect(page.locator(".sv-chart .c-guide--h")).to_have_count(1)
    series = page.locator(".sv-chart [class^='c-series-']")
    assert series.count() <= 5

    table = page.locator(".sv-tabella table")
    expect(table).to_be_visible()
    rows = page.locator(".sv-tabella tbody tr")
    expect(rows).to_have_count(11)


def test_usa_questo_valore_updates_field(page: Page, base_url: str) -> None:
    _open_tool(page, base_url)
    _open_sensibilita(page)
    page.locator("#sv-campo").select_option("h_mm")
    page.locator("#sv-da").fill("250")
    page.locator("#sv-a").fill("1000")
    page.locator("#sv-punti").fill("5")
    page.get_by_role("button", name="Calcola", exact=True).click()
    page.locator(".sv-tabella tbody tr").first.wait_for(state="visible", timeout=CALCOLA_TIMEOUT_MS)

    button = page.locator(".sv-usa").first
    button.click()
    expect(page.locator("#field-h_mm")).not_to_have_value("")


def test_keyboard_only_shortcut_opens_dialog(page: Page, base_url: str) -> None:
    _open_tool(page, base_url)
    page.locator("#field-h_mm").click()
    page.locator("#tool-title").click()
    page.keyboard.press("g")
    page.keyboard.press("s")
    page.locator(".sv-panel").wait_for(state="visible")
    expect(page.locator("#sv-campo")).to_have_value("h_mm")
