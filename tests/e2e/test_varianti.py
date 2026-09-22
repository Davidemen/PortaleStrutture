"""E2E coverage for WORKBENCH_SPEC.md §19: "Varianti affiancate" -- "Crea variante" and the strip
on the tool page, #/varianti/<tool> ("Affianca"), and "Tieni questa" (§19.4). Uses `demo-relazione`
(tests/e2e/_demo_tool.py): a checks list (verdict/eta max/verifica governante to compare) driven
by a single scalar input (`fattore`), small and deterministic.
"""
from __future__ import annotations

import re
import time

import pytest
from playwright.sync_api import Page, expect

from ._actions import field_id, goto_tool, load_example
from .test_progetti import create_project_via_ui, elemento_by_nome

pytestmark = pytest.mark.e2e

CREA_VARIANTE = "⧉ Crea variante"


def _unique(prefix: str) -> str:
    return f"{prefix} {time.time_ns()}"


def _open_demo_relazione(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)


def test_crea_variante_shows_strip_with_a_and_b(page: Page, base_url: str) -> None:
    _open_demo_relazione(page, base_url)
    expect(page.locator('[role="tablist"].vb-strip')).to_be_hidden()

    page.get_by_role("button", name=CREA_VARIANTE, exact=True).click()
    strip = page.locator('[role="tablist"].vb-strip')
    expect(strip).to_be_visible()
    tabs = strip.get_by_role("tab")
    expect(tabs).to_have_count(2)
    expect(tabs.nth(1)).to_have_attribute("aria-selected", "true")  # B becomes active (§19.2)


def test_crea_variante_stops_at_four_and_disables_the_button(page: Page, base_url: str) -> None:
    _open_demo_relazione(page, base_url)
    button = page.get_by_role("button", name=CREA_VARIANTE, exact=True)
    button.click()  # A, B
    button.click()  # C
    button.click()  # D
    expect(page.locator('[role="tablist"].vb-strip').get_by_role("tab")).to_have_count(4)
    expect(button).to_be_disabled()
    expect(button).to_have_attribute("title", "Massimo 4 varianti")


def test_affianca_shows_diff_and_deltas(page: Page, base_url: str) -> None:
    _open_demo_relazione(page, base_url)
    page.get_by_role("button", name=CREA_VARIANTE, exact=True).click()  # A, B active
    page.get_by_role("button", name=CREA_VARIANTE, exact=True).click()  # C active (copy of B)

    field = page.locator(field_id("fattore"))
    expect(field).to_have_value("2")
    field.fill("3")
    field.press("Tab")  # commits into the ACTIVE variant (C)

    page.get_by_role("button", name="Affianca", exact=True).click()
    expect(page).to_have_url(re.compile(r"#/varianti/demo-relazione$"))
    table = page.locator(".vc-table")
    expect(table).to_be_visible()
    expect(table.locator("thead th")).to_have_count(4)  # blank corner + A, B, C

    # Only one row of "Dati diversi" (fattore), and only C's cell is flagged.
    expect(page.get_by_text(re.compile(r"Dati diversi: 1 di \d+"))).to_be_visible()
    fattore_row = table.locator("tr", has_text="Fattore di carico applicato")
    expect(fattore_row.locator("td").nth(2)).to_contain_text("≠ diverso")
    expect(fattore_row.locator("td").nth(0)).not_to_contain_text("≠ diverso")

    # Every check's ratio is invariant to `fattore` (both value and limit scale with it), so the
    # eta max row shows no delta here -- but "Mostra tutti i risultati" reveals `somma_kN`, which
    # scales linearly with `fattore` and DOES differ (▲/▼ delta text, never colour alone).
    page.get_by_role("button", name="Mostra tutti i risultati", exact=True).click()
    somma_row = table.locator("tr", has_text="Somma dei valori")
    expect(somma_row.locator(".vc-delta").first).to_be_visible()


def test_reload_keeps_the_variant_set(page: Page, base_url: str) -> None:
    _open_demo_relazione(page, base_url)
    page.get_by_role("button", name=CREA_VARIANTE, exact=True).click()
    goto_tool(page, base_url, "demo-relazione")
    strip = page.locator('[role="tablist"].vb-strip')
    expect(strip).to_be_visible()
    expect(strip.get_by_role("tab")).to_have_count(2)


def test_chiudi_varianti_discards_the_set(page: Page, base_url: str) -> None:
    _open_demo_relazione(page, base_url)
    page.get_by_role("button", name=CREA_VARIANTE, exact=True).click()
    page.get_by_role("button", name="Chiudi varianti", exact=True).click()
    page.get_by_role("button", name="Chiudi e scarta", exact=True).click()
    expect(page.locator('[role="tablist"].vb-strip')).to_be_hidden()
    expect(page.get_by_role("button", name=CREA_VARIANTE, exact=True)).to_be_enabled()


def test_opening_elemento_with_open_varianti_asks_for_confirmation(page: Page, base_url: str) -> None:
    """§19.2: `?elemento=` must not silently overwrite an open varianti set -- "Annulla" leaves
    the strip untouched, "Chiudi e carica" applies the element and closes the set."""
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto varianti conferma"))
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    nome = _unique("Demo per conferma")
    from .test_progetti import save_current_tool_as_new_element

    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome=nome)
    elemento = elemento_by_nome(page, base_url, progetto_id, nome)

    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.get_by_role("button", name=CREA_VARIANTE, exact=True).click()
    strip = page.locator('[role="tablist"].vb-strip')
    expect(strip).to_be_visible()

    page.goto(f"{base_url}/#/demo-relazione?elemento={elemento['id']}")
    dialog = page.get_by_role("dialog", name="Chiudere le varianti aperte?")
    expect(dialog).to_be_visible()

    dialog.get_by_role("button", name="Annulla", exact=True).click()
    expect(dialog).to_be_hidden()
    expect(strip).to_be_visible()
    expect(strip.get_by_role("tab")).to_have_count(2)

    page.goto(f"{base_url}/#/demo-relazione?elemento={elemento['id']}")
    dialog = page.get_by_role("dialog", name="Chiudere le varianti aperte?")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name="Chiudi e carica", exact=True).click()
    expect(dialog).to_be_hidden()
    expect(page.locator('[role="tablist"].vb-strip')).to_be_hidden()


def test_tieni_questa_salva_come_nuovo_creates_one_element(page: Page, base_url: str) -> None:
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto varianti"))
    page.locator("#progetto-picker-select").select_option(progetto_id)
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.get_by_role("button", name=CREA_VARIANTE, exact=True).click()
    page.get_by_role("button", name="Affianca", exact=True).click()

    table = page.locator(".vc-table")
    expect(table).to_be_visible()
    table.locator(".vc-tieni").first.click()
    dialog = page.locator(".vt-dialog")
    expect(dialog).to_be_visible()
    nome = _unique("Demo variante A")
    dialog.locator(".vt-nome-input").fill(nome)
    dialog.get_by_role("button", name="Salva come nuovo elemento", exact=True).click()
    expect(dialog).to_be_hidden()

    elemento = elemento_by_nome(page, base_url, progetto_id, nome)
    assert elemento["strumento"] == "demo-relazione"


def test_tieni_questa_aggiorna_from_elemento_adds_a_revision(page: Page, base_url: str) -> None:
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto varianti aggiorna"))
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    nome = _unique("Demo per aggiorna")
    from .test_progetti import save_current_tool_as_new_element

    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome=nome)
    elemento = elemento_by_nome(page, base_url, progetto_id, nome)

    page.goto(f"{base_url}/#/demo-relazione?elemento={elemento['id']}")
    page.locator("#tool-title").wait_for(state="visible")
    page.get_by_role("button", name=CREA_VARIANTE, exact=True).click()  # A carries origine
    page.get_by_role("button", name="Affianca", exact=True).click()

    table = page.locator(".vc-table")
    table.locator(".vc-tieni").first.click()
    dialog = page.locator(".vt-dialog")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name=re.compile(r"^Aggiorna")).click()
    expect(dialog).to_be_hidden()

    revisioni = page.request.get(f"{base_url}/api/elementi/{elemento['id']}/revisioni")
    assert revisioni.status == 200, revisioni.text()
    body = revisioni.json()
    assert any("Variante A" in (r.get("nota") or "") for r in body), body


def test_tieni_questa_conflict_shows_the_dialog(page: Page, base_url: str) -> None:
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto varianti conflitto"))
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    nome = _unique("Demo per conflitto")
    from .test_progetti import save_current_tool_as_new_element

    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome=nome)
    elemento = elemento_by_nome(page, base_url, progetto_id, nome)

    page.goto(f"{base_url}/#/demo-relazione?elemento={elemento['id']}")
    page.locator("#tool-title").wait_for(state="visible")
    page.get_by_role("button", name=CREA_VARIANTE, exact=True).click()

    # A stale write behind the scenes -- the PUT this dialog is about to make will now conflict.
    put_body = {
        "strumento": elemento["strumento"],
        "nome": elemento["nome"],
        "inputs": elemento["inputs"],
        "sintesi": elemento["sintesi"],
        "stato": elemento["stato"],
        "modalita": elemento["modalita"],
        "provenienza": elemento["provenienza"],
        "sigla": elemento.get("sigla", ""),
        "nota": "Modificato da un altro utente",
        "revisione": elemento["revisione"],
    }
    response = page.request.put(f"{base_url}/api/elementi/{elemento['id']}", data=put_body)
    assert response.status == 200, response.text()

    page.get_by_role("button", name="Affianca", exact=True).click()
    page.locator(".vc-table .vc-tieni").first.click()
    dialog = page.locator(".vt-dialog")
    dialog.get_by_role("button", name=re.compile(r"^Aggiorna")).click()
    expect(page.get_by_role("heading", name="Conflitto di salvataggio")).to_be_visible()


def test_switching_variant_tabs_keeps_undo_isolated_per_variant(page: Page, base_url: str) -> None:
    """§21.1/§19.2: each variant's undo history is its own -- Ctrl+Z after switching to another
    variant must undo THAT variant's own last edit, never bleed the previous variant's step onto
    the newly active one's screen."""
    _open_demo_relazione(page, base_url)
    field = page.locator(field_id("fattore"))
    expect(field).to_have_value("2")

    page.get_by_role("button", name=CREA_VARIANTE, exact=True).click()  # A, B (B active)
    field.fill("5")
    field.press("Tab")
    expect(field).to_have_value("5")

    tabs = page.locator('[role="tablist"].vb-strip').get_by_role("tab")
    tabs.nth(0).click()  # back to A (still its original value)
    expect(field).to_have_value("2")

    field.fill("9")
    field.press("Tab")
    expect(field).to_have_value("9")

    page.keyboard.press("Control+z")
    expect(field).to_have_value("2")  # undoes A's OWN edit, not B's

    tabs.nth(1).click()  # to B: still 5, unaffected by A's undo
    expect(field).to_have_value("5")
    page.keyboard.press("Control+z")
    expect(field).to_have_value("2")  # B's own edit undone, its own pre-edit value
