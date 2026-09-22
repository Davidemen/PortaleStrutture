"""E2E coverage for WORKBENCH_SPEC.md §15: "Usa in..." typed links between tools. Provider
`sisma-parametri-sito` (example: categoria_sottosuolo=B, categoria_topografica=T1, ag_g=0.098,
f0=2.436) feeds `sito.categoria_sottosuolo`/`sito.categoria_topografica`/`sito.ag_g`/`sito.f0`
into two consumers, `muro-sostegno` and `fond-trave-collegamento` (src/strutture/shared/
collegamenti.py's registry, verified against the real, packaged tool models). The e2e server
(tests/e2e/_server.py) uses the REAL tool registry (`discover()`), so these links are the live
production ones, not a demo fixture.
"""
from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from ._actions import field_id, goto_tool, load_example
from ._collectors import PageCollectors

pytestmark = pytest.mark.e2e

PROVIDER = "sisma-parametri-sito"
CONSUMER = "muro-sostegno"
OTHER_CONSUMER = "fond-trave-collegamento"


def _sigla_of(page: Page, base_url: str, tool_name: str) -> str:
    response = page.request.get(f"{base_url}/api/tools")
    tool = next(item for item in response.json() if item["name"] == tool_name)
    return tool["sigla"]


def _open_usa_in_menu(page: Page) -> None:
    page.get_by_role("button", name="Usa in…").click()
    page.locator(".ui-menu").wait_for(state="visible")


def test_usa_in_button_lists_both_consumers(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, PROVIDER)
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")

    button = page.get_by_role("button", name="Usa in…")
    expect(button).to_be_visible()
    expect(button).to_have_attribute("aria-haspopup", "menu")
    expect(button).to_have_attribute("aria-expanded", "false")

    _open_usa_in_menu(page)
    expect(button).to_have_attribute("aria-expanded", "true")
    items = page.locator(".ui-menu-item")
    expect(items).to_have_count(2)
    expect(page.locator(f'.ui-menu-item[data-tool="{CONSUMER}"]')).to_have_count(1)
    expect(page.locator(f'.ui-menu-item[data-tool="{OTHER_CONSUMER}"]')).to_have_count(1)


def test_tool_without_consumers_shows_no_button(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "neve-carico-falda")
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    expect(page.get_by_role("button", name="Usa in…")).to_have_count(0)


def test_keyboard_escape_closes_menu_and_returns_focus(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, PROVIDER)
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    _open_usa_in_menu(page)

    page.keyboard.press("Escape")
    expect(page.locator(".ui-menu")).to_have_count(0)
    button = page.get_by_role("button", name="Usa in…")
    expect(button).to_have_attribute("aria-expanded", "false")
    assert page.evaluate("document.activeElement.classList.contains('ui-toggle')")


def test_choosing_consumer_prefills_chips_and_editing_clears_one(desktop_page: tuple[Page, PageCollectors], base_url: str) -> None:
    page, collectors = desktop_page
    provider_sigla = _sigla_of(page, base_url, PROVIDER)

    goto_tool(page, base_url, PROVIDER)
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    _open_usa_in_menu(page)
    page.locator(f'.ui-menu-item[data-tool="{CONSUMER}"]').click()

    page.wait_for_url(re.compile(rf"#/{CONSUMER}\?da={PROVIDER}"))
    page.locator("#tool-title").wait_for(state="visible")

    expect(page.locator(field_id("ag_g"))).to_have_value("0,098")
    expect(page.locator(field_id("f0"))).to_have_value("2,436")
    expect(page.locator(field_id("categoria_sottosuolo"))).to_have_value("B")
    expect(page.locator(field_id("categoria_topografica"))).to_have_value("T1")

    for name in ("ag_g", "f0", "categoria_sottosuolo", "categoria_topografica"):
        chip = page.locator(f'[data-field="{name}"] .pv-chip')
        expect(chip).to_have_text(f"da {provider_sigla}")

    note = page.locator(".pv-note")
    expect(note).to_be_visible()
    expect(note).to_contain_text("Dati ricevuti da")
    expect(note).to_contain_text("4 campi")

    # editing ag_g clears ONLY its own chip
    page.fill(field_id("ag_g"), "0.2")
    page.locator(field_id("ag_g")).blur()
    expect(page.locator('[data-field="ag_g"] .pv-chip')).to_have_count(0)
    expect(page.locator('[data-field="f0"] .pv-chip')).to_have_count(1)
    expect(page.locator('[data-field="categoria_sottosuolo"] .pv-chip')).to_have_count(1)
    expect(page.locator('[data-field="categoria_topografica"] .pv-chip')).to_have_count(1)

    # the note dismisses
    note.get_by_role("button", name="Chiudi").click()
    expect(note).to_be_hidden()

    assert collectors.console_errors == [], f"console.error calls: {collectors.console_errors}"
    assert collectors.page_errors == [], f"uncaught page errors: {collectors.page_errors}"


def test_saving_prefilled_consumer_into_project_stores_provenienza(page: Page, base_url: str) -> None:
    create_response = page.request.post(
        f"{base_url}/api/progetti", data={"codice": "", "nome": "Progetto usa-in", "committente": "", "note": ""}
    )
    assert create_response.status == 201, create_response.text()
    progetto_id = create_response.json()["id"]

    goto_tool(page, base_url, PROVIDER)
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    _open_usa_in_menu(page)
    page.locator(f'.ui-menu-item[data-tool="{CONSUMER}"]').click()
    page.locator("#tool-title").wait_for(state="visible")
    page.locator('[data-field="ag_g"] .pv-chip').wait_for(state="visible")

    page.get_by_role("button", name="Salva in progetto", exact=True).click()
    dialog = page.locator(".es-dialog")
    expect(dialog).to_be_visible()
    dialog.locator("#es-dialog-progetto").select_option(progetto_id)
    dialog.locator("#es-dialog-nome").fill("Muro con parametri di sito")
    dialog.get_by_role("button", name="Salva", exact=True).click()
    expect(dialog).to_be_hidden()

    elementi_response = page.request.get(f"{base_url}/api/progetti/{progetto_id}/elementi")
    assert elementi_response.status == 200, elementi_response.text()
    elemento = elementi_response.json()[0]
    collegamenti = elemento["provenienza"]["collegamenti"]
    chiavi = {c["chiave"] for c in collegamenti}
    assert chiavi == {"sito.ag_g", "sito.f0", "sito.categoria_sottosuolo", "sito.categoria_topografica"}, collegamenti
    assert all(c["strumento"] == PROVIDER for c in collegamenti), collegamenti
