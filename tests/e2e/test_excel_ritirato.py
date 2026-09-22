"""E2E coverage for WORKBENCH_SPEC.md §16: Excel mode retires per approved tool. Uses
`acciaio-resistenza-incendio`, whose real, packaged register has exactly ONE entry
(`acciaio-incendio/fu-s275-mai-selezionato`, unique to this tool) -- approving/rejecting it here
never affects any other test's counts. The e2e server (tests/e2e/_server.py) uses a fresh
`InMemorySignoffRepository` and the REAL register (`load_register()`); every test resets the
entry back to `da_confermare` when it is done, so later tests still see the packaged default.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool, load_example

pytestmark = pytest.mark.e2e

TOOL = "acciaio-resistenza-incendio"
DIVERGENCE_ID = "acciaio-incendio/fu-s275-mai-selezionato"
LEGACY_FIELD = '[data-field="legacy_compat"]'


def _signoff(page: Page, base_url: str, stato: str, *, sigla: str = "") -> None:
    response = page.request.post(
        f"{base_url}/api/divergences/signoff-multiplo",
        data={"ids": [DIVERGENCE_ID], "stato": stato, "sigla": sigla, "nota": ""},
    )
    assert response.status == 200, response.text()


def _open_avanzate(page: Page) -> None:
    page.locator("#form-root .f-advanced > summary").click()


def test_approved_tool_hides_switch_and_compare_button(page: Page, base_url: str) -> None:
    _signoff(page, base_url, "approvato", sigla="AB")
    try:
        goto_tool(page, base_url, TOOL)
        load_example(page)
        page.locator("#results-head").wait_for(state="visible")

        # the Avanzate fold itself is hidden (the switch was its only field) -- not just closed.
        expect(page.locator("#form-root .f-advanced")).to_be_hidden()
        expect(page.locator(LEGACY_FIELD)).to_be_hidden()
        expect(page.locator(".cf-toggle")).to_have_count(0)

        indicator = page.locator("#tool-registro-indicator")
        expect(indicator).to_contain_text("Correzioni approvate")
    finally:
        _signoff(page, base_url, "da_confermare")


def test_share_link_with_legacy_compat_true_is_forced_off(page: Page, base_url: str) -> None:
    _signoff(page, base_url, "approvato", sigla="AB")
    try:
        page.goto(f"{base_url}/#/{TOOL}?legacy_compat=true")
        page.locator("#tool-title").wait_for(state="visible")
        page.locator("#form-root .f-section-toggle, #form-root .f-field").first.wait_for(state="visible")

        note = page.locator(".xr-note")
        expect(note).to_be_visible()
        expect(note).to_contain_text("Modalità Excel non più disponibile")
        expect(page.locator("#form-root .f-advanced")).to_be_hidden()
        expect(page.locator(LEGACY_FIELD)).to_be_hidden()

        note.get_by_role("button", name="Chiudi").click()
        expect(note).to_be_hidden()
    finally:
        _signoff(page, base_url, "da_confermare")


def test_rejecting_one_entry_brings_controls_back_after_reload(page: Page, base_url: str) -> None:
    _signoff(page, base_url, "approvato", sigla="AB")
    try:
        goto_tool(page, base_url, TOOL)
        load_example(page)
        page.locator("#results-head").wait_for(state="visible")
        expect(page.locator(LEGACY_FIELD)).to_be_hidden()

        _signoff(page, base_url, "respinto", sigla="CD")

        page.reload()
        page.locator("#tool-title").wait_for(state="visible")
        load_example(page)
        page.locator("#results-head").wait_for(state="visible")

        _open_avanzate(page)
        expect(page.locator("#form-root .f-advanced")).to_be_visible()
        expect(page.locator(LEGACY_FIELD)).to_be_visible()
        expect(page.locator(".cf-toggle")).to_have_count(1)
    finally:
        _signoff(page, base_url, "da_confermare")
