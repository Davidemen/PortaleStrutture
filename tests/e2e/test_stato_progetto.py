"""E2E coverage for WORKBENCH_SPEC.md §25: "da ricalcolare" (§25.1/§25.4) surfaced on the project
table -- `GET /api/progetti/{id}/stato` is already exercised end-to-end at the unit/API level
(tests/shared/stato_progetto/, tests/web/test_progetti_stato_api.py); this file only proves the UI
plumbing: "Usa in..." into a saved provider stores `elemento_id`/`revisione_fornitore`, the badge
appears once the provider's saved inputs change, and a resave that only renames the consumer never
clears it (§25.1, "no save ever clears the provenance of an item the user did not touch").

`sisma-parametri-sito` -> `muro-sostegno` is the SAME pair WORKBENCH_SPEC §25.5's own acceptance
uses; the e2e server (tests/e2e/_server.py) runs the real tool registry, so these are the live
production links.
"""
from __future__ import annotations

import re
import time

import pytest
from playwright.sync_api import Page, expect

from ._actions import field_id, goto_tool, load_example

pytestmark = pytest.mark.e2e

PROVIDER = "sisma-parametri-sito"
CONSUMER = "muro-sostegno"


def _unique(prefix: str) -> str:
    return f"{prefix} {time.time_ns()}"


def _create_project(page: Page, base_url: str, nome: str) -> str:
    response = page.request.post(f"{base_url}/api/progetti", data={"codice": "", "nome": nome, "committente": "", "note": ""})
    assert response.status == 201, response.text()
    return response.json()["id"]


def _save_as_new(page: Page, *, progetto_id: str, nome: str) -> None:
    trigger_name = "Salva come nuovo" if page.get_by_role("button", name="Salva", exact=True).count() > 0 else "Salva in progetto"
    page.get_by_role("button", name=trigger_name, exact=True).click()
    dialog = page.locator(".es-dialog")
    expect(dialog).to_be_visible()
    dialog.locator("#es-dialog-progetto").select_option(progetto_id)
    dialog.locator("#es-dialog-nome").fill(nome)
    dialog.get_by_role("button", name="Salva", exact=True).click()
    expect(dialog).to_be_hidden()


def _save_existing(page: Page) -> None:
    page.get_by_role("button", name="Salva", exact=True).click()
    expect(page.locator(".es-status")).to_contain_text("salvato")


def test_provider_value_change_marks_consumer_da_ricalcolare(page: Page, base_url: str) -> None:
    progetto_id = _create_project(page, base_url, _unique("Progetto stato"))

    goto_tool(page, base_url, PROVIDER)
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    _save_as_new(page, progetto_id=progetto_id, nome=_unique("Sito"))

    page.get_by_role("button", name="Usa in…").click()
    page.locator(".ui-menu").wait_for(state="visible")
    page.locator(f'.ui-menu-item[data-tool="{CONSUMER}"]').click()
    page.wait_for_url(re.compile(rf"#/{CONSUMER}\?da={PROVIDER}"))
    page.locator("#tool-title").wait_for(state="visible")
    page.locator('[data-field="ag_g"] .pv-chip').wait_for(state="visible")
    nome_muro = _unique("Muro")
    _save_as_new(page, progetto_id=progetto_id, nome=nome_muro)

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    muro_row = page.locator(f'.pt-row:has-text("{nome_muro}")')
    expect(muro_row.locator(".pst-chip--ricalcola")).to_have_count(0)

    # change the provider's own saved value and resave (new revisione, ag_g actually different)
    provider_row = page.locator(".pt-row").filter(has_text="Sito")
    provider_row.locator(".pt-cell-nome a").click()
    page.locator("#tool-title").wait_for(state="visible")
    page.fill(field_id("ag_g"), "0.2")
    page.locator(field_id("ag_g")).blur()
    expect(page.locator("#results-root")).not_to_have_class(re.compile("r-sheet--stale"))
    _save_existing(page)

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    muro_row = page.locator(f'.pt-row:has-text("{nome_muro}")')
    expect(muro_row.locator(".pst-chip--ricalcola")).to_have_text("↻ Da ricalcolare")
    # §25.1/§25.4: the tooltip names the provider by its SIGLA ("SPS"), never the raw tool slug.
    titolo = muro_row.locator(".pst-chip--ricalcola").get_attribute("title")
    assert "da SPS" in titolo, titolo
    assert PROVIDER not in titolo, titolo


def test_rename_only_resave_keeps_da_ricalcolare_marker(page: Page, base_url: str) -> None:
    progetto_id = _create_project(page, base_url, _unique("Progetto rinomina"))

    goto_tool(page, base_url, PROVIDER)
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    _save_as_new(page, progetto_id=progetto_id, nome=_unique("Sito2"))

    page.get_by_role("button", name="Usa in…").click()
    page.locator(".ui-menu").wait_for(state="visible")
    page.locator(f'.ui-menu-item[data-tool="{CONSUMER}"]').click()
    page.wait_for_url(re.compile(rf"#/{CONSUMER}\?da={PROVIDER}"))
    page.locator("#tool-title").wait_for(state="visible")
    page.locator('[data-field="ag_g"] .pv-chip').wait_for(state="visible")
    nome_muro = _unique("Muro2")
    _save_as_new(page, progetto_id=progetto_id, nome=nome_muro)

    # change the provider and resave -- the wall is now da ricalcolare
    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    page.locator(".pt-row").filter(has_text="Sito2").locator(".pt-cell-nome a").click()
    page.locator("#tool-title").wait_for(state="visible")
    page.fill(field_id("ag_g"), "0.3")
    page.locator(field_id("ag_g")).blur()
    expect(page.locator("#results-root")).not_to_have_class(re.compile("r-sheet--stale"))
    _save_existing(page)

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    muro_row = page.locator(f'.pt-row:has-text("{nome_muro}")')
    expect(muro_row.locator(".pst-chip--ricalcola")).to_have_text("↻ Da ricalcolare")

    # rename the wall (Azioni -> Rinomina) without touching any field -- the marker must survive
    muro_row.locator(".pt-azioni-btn").click()
    muro_row.get_by_role("menuitem", name="Rinomina").click()
    nuovo_nome = f"{nome_muro} (rinominato)"
    muro_row.locator(".pt-inline-input").fill(nuovo_nome)
    muro_row.get_by_role("button", name="Salva").click()

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    renamed_row = page.locator(f'.pt-row:has-text("{nuovo_nome}")')
    expect(renamed_row.locator(".pst-chip--ricalcola")).to_have_text("↻ Da ricalcolare")
