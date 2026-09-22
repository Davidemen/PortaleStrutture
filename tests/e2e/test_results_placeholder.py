"""The empty results pane's placeholder matches the calculation mode (owner's finding, 2026-09-22):
with live calculation on nobody has to press "Calcola", so the text must not say so."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool

pytestmark = pytest.mark.e2e

LIVE = "Compila i dati: il calcolo parte da solo. Oppure carica l'esempio."
MANUAL = "Compila i dati e premi Calcola. Oppure carica l'esempio."


def test_placeholder_follows_the_live_toggle(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "vento-cpe-rettangolare")
    placeholder = page.locator("#results-root .r-empty")
    expect(placeholder).to_have_text(LIVE)  # live calculation is on by default
    page.locator("#live-toggle").uncheck()
    expect(placeholder).to_have_text(MANUAL)
    expect(page.get_by_role("button", name="Calcola", exact=True)).to_be_visible()
    page.reload()
    expect(page.locator("#results-root .r-empty")).to_have_text(MANUAL)  # the setting is persisted
    page.locator("#live-toggle").check()
    expect(page.locator("#results-root .r-empty")).to_have_text(LIVE)
