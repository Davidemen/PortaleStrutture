"""E2E coverage for WORKBENCH_SPEC.md §20: the project page's element table (js/progetto-
tabella.js + js/progetto-tabella-dati.js) -- η max/esito/avvisi cells, sort, filters, the hash
query surviving reload/Back, keyboard opening a row, "n.d." for a pre-§20.1 element, and that
simply opening the page never triggers a `/run` (the table only ever READS saved summaries).
"""
from __future__ import annotations

import re
import time

import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool, load_example

pytestmark = pytest.mark.e2e


def _unique(prefix: str) -> str:
    return f"{prefix} {time.time_ns()}"


def _create_project(page: Page, base_url: str, nome: str) -> str:
    response = page.request.post(f"{base_url}/api/progetti", data={"codice": "", "nome": nome, "committente": "", "note": ""})
    assert response.status == 201, response.text()
    return response.json()["id"]


def _save_current_as(page: Page, *, progetto_id: str, nome: str) -> None:
    page.get_by_role("button", name="Salva in progetto", exact=True).click()
    dialog = page.locator(".es-dialog")
    expect(dialog).to_be_visible()
    dialog.locator("#es-dialog-progetto").select_option(progetto_id)
    dialog.locator("#es-dialog-nome").fill(nome)
    dialog.get_by_role("button", name="Salva", exact=True).click()
    expect(dialog).to_be_hidden()


def _post_bare_element(page: Page, base_url: str, progetto_id: str, nome: str) -> dict:
    """An element POSTed WITHOUT `sintesi.avvisi` (§20.1: "elements saved before this change")."""
    body = {
        "strumento": "demo-tabella", "nome": nome, "inputs": {"stratigrafia": []},
        "sintesi": {"ok": True}, "stato": "verificato", "modalita": "standard", "provenienza": {},
        "sigla": "", "nota": "",
    }
    response = page.request.post(f"{base_url}/api/progetti/{progetto_id}/elementi", data=body)
    assert response.status == 201, response.text()
    return response.json()


def _open_progetto(page: Page, base_url: str, progetto_id: str) -> None:
    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")


def test_table_shows_esito_eta_and_avvisi_and_no_run_request(page: Page, base_url: str) -> None:
    progetto_id = _create_project(page, base_url, _unique("Progetto tabella"))

    goto_tool(page, base_url, "demo-tabella")
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    _save_current_as(page, progetto_id=progetto_id, nome="Verificato senza avvisi")

    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    _save_current_as(page, progetto_id=progetto_id, nome="Con avvisi ed errore di verifica")

    _post_bare_element(page, base_url, progetto_id, "Elemento pre-§20.1")

    run_requests = []
    page.on("request", lambda request: run_requests.append(request.url) if "/run" in request.url else None)
    _open_progetto(page, base_url, progetto_id)
    assert run_requests == [], f"the table must never trigger a run: {run_requests}"

    rows = page.locator(".pt-row")
    expect(rows).to_have_count(3)

    verificato_row = page.locator('.pt-row:has-text("Verificato senza avvisi")')
    expect(verificato_row.locator(".pt-cell-esito")).to_have_text("✓ Verificato")
    expect(verificato_row.locator(".pt-cell-eta")).to_have_text("—")
    expect(verificato_row.locator(".pt-cell-avvisi")).to_have_text("Nessuno")

    avvisi_row = page.locator('.pt-row:has-text("Con avvisi ed errore di verifica")')
    expect(avvisi_row.locator(".pt-cell-esito")).to_have_text("✕ Non verificato")
    expect(avvisi_row.locator(".pt-cell-avvisi")).to_contain_text("1 · Avviso di prova")

    nd_row = page.locator('.pt-row:has-text("Elemento pre-§20.1")')
    expect(nd_row.locator(".pt-cell-avvisi")).to_have_text("n.d.")


def test_sort_by_eta_puts_missing_last_and_filters_narrow_the_table(page: Page, base_url: str) -> None:
    progetto_id = _create_project(page, base_url, _unique("Progetto filtri"))

    goto_tool(page, base_url, "demo-tabella")
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    _save_current_as(page, progetto_id=progetto_id, nome="Senza eta")

    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    _save_current_as(page, progetto_id=progetto_id, nome="Con eta")

    _open_progetto(page, base_url, progetto_id)

    page.get_by_role("button", name=re.compile(r"^η max")).click()  # first click: descending
    rows = page.locator(".pt-row .pt-cell-nome")
    expect(rows.nth(0)).to_contain_text("Con eta")
    expect(rows.nth(1)).to_contain_text("Senza eta")

    page.locator(".pt-filter-esito").select_option("non_verificato")
    expect(page.locator(".pt-row")).to_have_count(1)
    expect(page.locator(".pt-row")).to_contain_text("Con eta")

    page.locator(".pt-filter-clear").click()
    expect(page.locator(".pt-row")).to_have_count(2)

    page.locator("#pt-filter-avvisi").check()
    expect(page.locator(".pt-row")).to_have_count(1)
    expect(page.locator(".pt-row")).to_contain_text("Con eta")


def test_query_survives_reload_and_back(page: Page, base_url: str) -> None:
    progetto_id = _create_project(page, base_url, _unique("Progetto query"))
    goto_tool(page, base_url, "demo-tabella")
    load_example(page)
    page.locator("#results-head").wait_for(state="visible")
    _save_current_as(page, progetto_id=progetto_id, nome="Elemento query")

    _open_progetto(page, base_url, progetto_id)
    page.locator(".pt-filter-q").fill("query")
    page.wait_for_url(re.compile(r"q=query"))

    page.reload()
    page.locator(".pt-table").wait_for(state="visible")
    expect(page.locator(".pt-filter-q")).to_have_value("query")

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.go_back()
    page.locator(".pt-table").wait_for(state="visible")
    expect(page.locator(".pt-filter-q")).to_have_value("query")


def test_keyboard_down_down_enter_opens_the_right_element(page: Page, base_url: str) -> None:
    progetto_id = _create_project(page, base_url, _unique("Progetto tastiera"))
    for nome in ("Alfa", "Beta"):
        goto_tool(page, base_url, "demo-tabella")
        load_example(page)
        page.locator("#results-head").wait_for(state="visible")
        _save_current_as(page, progetto_id=progetto_id, nome=nome)

    _open_progetto(page, base_url, progetto_id)
    page.get_by_role("button", name=re.compile(r"^Nome")).click()  # sort by nome ascending
    first_link = page.locator(".pt-cell-nome a").first
    first_link.focus()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    page.wait_for_url(re.compile(r"#/demo-tabella\?elemento="))
