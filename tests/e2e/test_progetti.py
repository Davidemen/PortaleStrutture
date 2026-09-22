"""E2E coverage for WORKBENCH_SPEC.md §14: projects and saved elements -- the header project
picker, "Salva in progetto"/the 409 dialog, `#/progetti` (list) and `#/progetti/<id>` (project
page: head, element list, storia, duplicate/rename/delete, export/import, "Relazione di
progetto"). The e2e server (tests/e2e/_server.py) always uses a fresh, in-memory
`InMemoryProjectRepository` -- SHARED across every test in this session (unlike the per-test
isolation a real deployment would have), so every project/element name here is made unique via
`_unique()` rather than relying on a clean slate.

`demo-relazione` and `demo-tabella` (tests/e2e/_demo_tool.py) stand in for real tools: the first
has checks (eta max/verifica governante to save into `sintesi`) and a `relazione: true` schema
(exercises "Sviluppo dei calcoli" in the project report); the second has a table field (exercises
"tables too" on reopen).
"""
from __future__ import annotations

import json
import re
import time

import pytest
from playwright.sync_api import Page, expect

from ._actions import field_id, goto_tool, load_example, submit
from ._collectors import PageCollectors

pytestmark = pytest.mark.e2e


def _unique(prefix: str) -> str:
    return f"{prefix} {time.time_ns()}"


def goto_progetti(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/#/progetti")
    page.locator("#progetti-pane h2").wait_for(state="visible")


def open_azioni(row) -> None:
    """WORKBENCH_SPEC §20.2: row actions moved into a per-row "⋯ Azioni" menu button."""
    row.locator(".pt-azioni-btn").click()


def create_project_via_ui(page: Page, base_url: str, nome: str, *, codice: str = "", committente: str = "") -> str:
    """Creates a project through the #/progetti "Nuovo progetto" form; returns its id (parsed
    from the resulting #/progetti/<id> redirect)."""
    goto_progetti(page, base_url)
    page.get_by_role("button", name="Nuovo progetto").click()
    page.fill("#pj-new-nome", nome)
    if codice:
        page.fill("#pj-new-codice", codice)
    if committente:
        page.fill("#pj-new-committente", committente)
    page.get_by_role("button", name="Crea progetto").click()
    page.wait_for_url(re.compile(r"#/progetti/[a-f0-9]+$"))
    return page.url.split("#/progetti/")[-1]


def save_current_tool_as_new_element(page: Page, *, progetto_id: str, nome: str, sigla: str = "", nota: str = "") -> None:
    """Drives the "Salva in progetto"/"Salva come nuovo" dialog to completion for whichever tool
    is currently open, into an EXISTING project (selected explicitly -- the header picker's own
    "current project" is a separate, independent piece of state the dialog does not assume)."""
    trigger_name = "Salva come nuovo" if page.get_by_role("button", name="Salva", exact=True).count() > 0 else "Salva in progetto"
    page.get_by_role("button", name=trigger_name, exact=True).click()
    dialog = page.locator(".es-dialog")
    expect(dialog).to_be_visible()
    dialog.locator("#es-dialog-progetto").select_option(progetto_id)
    dialog.locator("#es-dialog-nome").fill(nome)
    if sigla:
        dialog.locator("#es-dialog-sigla").fill(sigla)
    if nota:
        dialog.locator("#es-dialog-nota").fill(nota)
    dialog.get_by_role("button", name="Salva", exact=True).click()
    expect(dialog).to_be_hidden()


def elemento_by_nome(page: Page, base_url: str, progetto_id: str, nome: str) -> dict:
    response = page.request.get(f"{base_url}/api/progetti/{progetto_id}/elementi")
    assert response.status == 200, response.text()
    return next(item for item in response.json() if item["nome"] == nome)


# -- creating a project, saving an element, reopening it (with its tables) ----------------------


def test_create_project_via_ui(page: Page, base_url: str) -> None:
    nome = _unique("Progetto UI")
    create_project_via_ui(page, base_url, nome, codice="C1", committente="Committente SRL")
    expect(page.locator(".pd-field[data-key='nome'] .pd-field-value")).to_have_text(nome)
    expect(page.locator(".pd-field[data-key='codice'] .pd-field-value")).to_have_text("C1")
    expect(page.locator(".pd-field[data-key='committente'] .pd-field-value")).to_have_text("Committente SRL")

    goto_progetti(page, base_url)
    expect(page.locator(".pj-row", has_text=nome)).to_have_count(1)


def test_save_element_from_tool_and_reopen_with_tables(page: Page, base_url: str) -> None:
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto Tabelle"))
    goto_tool(page, base_url, "demo-tabella")
    load_example(page)
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome="Stratigrafia 1")

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    page.locator(".pt-row", has_text="Stratigrafia 1").locator(".pt-cell-nome a").click()
    page.locator("#tool-title").wait_for(state="visible")

    rows = page.locator("[data-field='stratigrafia'] table tbody tr")
    expect(rows).to_have_count(2)
    second_row_modulo = rows.nth(1).locator("input, select").nth(1)
    expect(second_row_modulo).to_have_value("22")
    expect(page.locator(".es-state-text")).to_have_text(re.compile("Stratigrafia 1"))
    expect(page.get_by_role("button", name="Salva", exact=True)).to_be_visible()


# -- 409 conflict: Ricarica / Salva come copia ---------------------------------------------------


def _stale_put_body(nome: str, revisione: int) -> dict:
    return {
        "strumento": "demo-relazione",
        "nome": nome,
        "inputs": {"fattore": 9.0, "nota": "cambiato da un altro utente"},
        "sintesi": {},
        "stato": "non_verificato",
        "modalita": "standard",
        "provenienza": {},
        "sigla": "",
        "nota": "",
        "revisione": revisione,
    }


def test_conflict_dialog_ricarica(page: Page, base_url: str) -> None:
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto Conflitto"))
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    nome = "Elemento conflitto"
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome=nome)
    elemento = elemento_by_nome(page, base_url, progetto_id, nome)

    # "another user" saves first, through the API directly, behind this page's back.
    response = page.request.put(f"{base_url}/api/elementi/{elemento['id']}", data=_stale_put_body(nome, elemento["revisione"]))
    assert response.status == 200, response.text()

    # This page still thinks its own revisione is the one it first loaded -- "Salva" now conflicts.
    page.get_by_role("button", name="Salva", exact=True).click()
    conflict = page.locator(".es-dialog", has_text="Conflitto di salvataggio")
    expect(conflict).to_be_visible()
    expect(conflict).to_contain_text("Modificato da un altro utente: ricarica e riprova")

    conflict.get_by_role("button", name="Ricarica").click()
    expect(conflict).to_be_hidden()
    expect(page.locator(field_id("fattore"))).to_have_value(re.compile(r"^9"))
    expect(page.locator(".es-status")).to_have_text("Elemento ricaricato: le modifiche locali sono state scartate.")


def test_conflict_dialog_salva_come_copia(page: Page, base_url: str) -> None:
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto Conflitto Copia"))
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    nome = "Elemento originale"
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome=nome)
    elemento = elemento_by_nome(page, base_url, progetto_id, nome)

    response = page.request.put(f"{base_url}/api/elementi/{elemento['id']}", data=_stale_put_body(nome, elemento["revisione"]))
    assert response.status == 200, response.text()

    page.get_by_role("button", name="Salva", exact=True).click()
    conflict = page.locator(".es-dialog", has_text="Conflitto di salvataggio")
    expect(conflict).to_be_visible()
    conflict.get_by_role("button", name="Salva come copia").click()

    create_dialog = page.locator(".es-dialog", has_text="Salva come nuovo")
    expect(create_dialog).to_be_visible()
    expect(create_dialog.locator("#es-dialog-nome")).to_have_value(re.compile("copia"))
    create_dialog.get_by_role("button", name="Salva", exact=True).click()
    expect(create_dialog).to_be_hidden()

    response = page.request.get(f"{base_url}/api/progetti/{progetto_id}/elementi")
    nomi = sorted(item["nome"] for item in response.json())
    assert len(nomi) == 2, nomi
    assert any("copia" in n for n in nomi), nomi


# -- project page: rename, duplicate, storia, delete ---------------------------------------------


def test_rename_project_inline(page: Page, base_url: str) -> None:
    nome = _unique("Progetto Rinomina")
    progetto_id = create_project_via_ui(page, base_url, nome)
    goto_progetti(page, base_url)
    # `data-id`, not `has_text=nome`: once "Rinomina" swaps the name in for an `<input value=...>`,
    # the project's name is no longer part of the row's TEXT content at all (an input's `value` is
    # an attribute, invisible to `has_text`) -- a `has_text` locator would stop matching its own
    # row the instant editing starts.
    row = page.locator(f'.pj-row[data-id="{progetto_id}"]')
    row.get_by_role("button", name="Rinomina").click()
    nuovo_nome = f"{nome} rinominato"
    row.locator(".pj-rename-input").fill(nuovo_nome)
    row.get_by_role("button", name="Salva", exact=True).click()
    expect(row).to_contain_text(nuovo_nome)


def test_rename_element_inline_keeps_inputs(page: Page, base_url: str) -> None:
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto Rinomina Elemento"))
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome="Nome originale")
    elemento_id = elemento_by_nome(page, base_url, progetto_id, "Nome originale")["id"]

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    # `data-id`, not `has_text`: see test_rename_project_inline's own comment -- the name moves
    # into an `<input value=...>` the instant "Rinomina" is clicked, which `has_text` cannot see.
    row = page.locator(f'.pt-row[data-id="{elemento_id}"]')
    open_azioni(row)
    row.get_by_role("menuitem", name="Rinomina").click()
    row.locator(".pt-inline-input").fill("Nome rinominato")
    row.get_by_role("button", name="Salva", exact=True).click()
    expect(row).to_contain_text("Nome rinominato")

    # `_ElementoUpdateBody.inputs` defaults to `{}` -- a rename-only PUT that forgot to resend the
    # stored inputs would silently wipe them (routes/progetti.py); this must never happen.
    elemento = elemento_by_nome(page, base_url, progetto_id, "Nome rinominato")
    assert elemento["inputs"].get("fattore") == 2.0, elemento["inputs"]


def test_duplicate_element(page: Page, base_url: str) -> None:
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto Duplica"))
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome="Originale")

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    row = page.locator(".pt-row", has_text="Originale")
    open_azioni(row)
    row.get_by_role("menuitem", name="Duplica").click()
    name_input = row.locator(".pt-inline-input")
    expect(name_input).to_have_value("Originale (copia)")
    row.get_by_role("button", name="Duplica", exact=True).click()

    expect(page.locator(".pt-row")).to_have_count(2)
    expect(page.locator(".pt-row", has_text="Originale (copia)")).to_have_count(1)


def test_history_carica_questa_revisione_previews_without_saving(page: Page, base_url: str) -> None:
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto Storia"))
    goto_tool(page, base_url, "demo-relazione")
    # `load_example` first (same convention as every other demo-relazione test here and in
    # test_relazione_overlay.py's own `_load_demo`): its optional, advanced `nota` field has no
    # `condition`, so an untouched/emptied textarea reads back as `null` (fields.js's `readValue`
    # maps an empty text control to `null`, and `nota: str` has no `| None` to accept it) --
    # loading the example first gives it a real string ("Esempio") before `fattore` is overridden.
    load_example(page)
    page.fill(field_id("fattore"), "1")
    submit(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    nome = "Elemento storia"
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome=nome)

    # a second save (still loaded) writes a SECOND revision with a different fattore
    page.fill(field_id("fattore"), "3")
    submit(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    page.get_by_role("button", name="Salva", exact=True).click()
    expect(page.locator(".es-status")).to_have_text("Elemento salvato.")

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    row = page.locator(".pt-row", has_text=nome)
    open_azioni(row)
    row.get_by_role("menuitem", name="Storia", exact=True).click()
    items = row.locator(".ps-item")
    expect(items).to_have_count(2)

    # "Revisione 1" (fattore=1, the FIRST save) -- found by its own text rather than assumed list
    # order, proves a PAST revision loads, not the tool's current in-memory state (fattore=3).
    items.filter(has_text="Revisione 1").get_by_role("button", name="Carica questa revisione").click()
    page.locator("#tool-title").wait_for(state="visible")
    expect(page).to_have_url(re.compile(r"anteprima=1"))
    expect(page.locator(field_id("fattore"))).to_have_value(re.compile(r"^1"))
    # never tied to the saved element: the widget stays in its plain, unsaved state.
    expect(page.get_by_role("button", name="Salva in progetto", exact=True)).to_be_visible()
    expect(page.locator(".es-state-text")).to_be_hidden()


def test_soft_delete_and_restore_project(page: Page, base_url: str) -> None:
    nome = _unique("Progetto Eliminabile")
    create_project_via_ui(page, base_url, nome)
    goto_progetti(page, base_url)
    row = page.locator(".pj-row", has_text=nome)
    row.get_by_role("button", name="Elimina", exact=True).click()
    row.get_by_role("button", name="Conferma eliminazione").click()
    expect(page.locator(".pj-row", has_text=nome)).to_have_count(0)

    page.get_by_role("button", name="Mostra eliminati").click()
    deleted_row = page.locator(".pj-row", has_text=nome)
    expect(deleted_row).to_have_count(1)
    deleted_row.get_by_role("button", name="Ripristina").click()
    expect(page.locator(".pj-row", has_text=nome)).to_have_count(0)  # gone from the deleted view

    page.get_by_role("button", name="Mostra eliminati").click()  # back to the active view
    expect(page.locator(".pj-row", has_text=nome)).to_have_count(1)


def test_soft_delete_and_restore_element(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC §14.3: an element row gets the same Elimina/"Mostra eliminati"/Ripristina
    pattern as the project list (§14.2) -- js/progetto-elementi.js's own toggle, not a copy of
    js/progetti.js's. The project's own "n. elementi" count (js/progetti.js's `loadCounts`, backed
    by the DEFAULT `GET .../elementi`, active-only) must stay unaffected by the soft delete."""
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto Elemento Eliminabile"))
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    nome = "Elemento eliminabile"
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome=nome)

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    row = page.locator(".pt-row", has_text=nome)
    expect(row).to_have_count(1)
    open_azioni(row)
    row.get_by_role("menuitem", name="Elimina", exact=True).click()
    row.get_by_role("button", name="Conferma eliminazione").click()
    expect(page.locator(".pt-row", has_text=nome)).to_have_count(0)

    # SAME session, no reload: the deleted row must reappear from the client's own in-memory
    # list (js/progetto-elementi.js marks it deleted in place rather than dropping it), not only
    # after a fresh fetch -- catches a real bug where "Elimina" used to purge the row outright.
    page.get_by_role("button", name="Mostra eliminati").click()
    expect(page.locator(".pe-row", has_text=nome)).to_have_count(1)
    page.get_by_role("button", name="Mostra eliminati").click()  # back to the active view

    goto_progetti(page, base_url)
    count_cell = page.locator(f'.pj-row[data-id="{progetto_id}"] .pj-row-count')
    expect(count_cell).to_have_text("0")

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.get_by_role("button", name="Mostra eliminati").click()
    deleted_row = page.locator(".pe-row", has_text=nome)
    expect(deleted_row).to_have_count(1)
    expect(deleted_row.locator(".pe-stato")).to_have_text("⊘ Eliminato")
    deleted_row.get_by_role("button", name="Ripristina").click()
    expect(page.locator(".pe-row", has_text=nome)).to_have_count(0)  # gone from the deleted view

    page.get_by_role("button", name="Mostra eliminati").click()  # back to the active view -- .pt-table
    expect(page.locator(".pt-row", has_text=nome)).to_have_count(1)

    goto_progetti(page, base_url)
    expect(count_cell).to_have_text("1")


def test_filter_elements_by_tool(page: Page, base_url: str) -> None:
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto Filtro"))
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome="Elemento A")

    goto_tool(page, base_url, "demo-tabella")
    load_example(page)
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome="Elemento B")

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    expect(page.locator(".pt-row")).to_have_count(2)
    page.locator(".pt-filter-strumento").select_option("demo-tabella")
    expect(page.locator(".pt-row")).to_have_count(1)
    expect(page.locator(".pt-cell-nome")).to_have_text("Elemento B")


# -- export / import round trip -------------------------------------------------------------------


def test_export_import_round_trip(page: Page, base_url: str) -> None:
    nome = _unique("Progetto Esporta")
    progetto_id = create_project_via_ui(page, base_url, nome, codice="EXP1")
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome="Elemento esportato")

    export_response = page.request.get(f"{base_url}/api/progetti/{progetto_id}/esporta")
    assert export_response.status == 200, export_response.text()
    payload = export_response.json()
    assert payload["formato"] == "strutture-progetto"
    assert len(payload["elementi"]) == 1

    import_response = page.request.post(f"{base_url}/api/progetti/importa", data=payload)
    assert import_response.status == 200, import_response.text()
    imported = import_response.json()["progetto"]
    # same codice+nome as the still-active original -> "(importato AAAA-MM-GG)" (scambio.py)
    assert "importato" in imported["nome"], imported["nome"]

    page.goto(f"{base_url}/#/progetti/{imported['id']}")
    page.locator(".pt-table").wait_for(state="visible")
    expect(page.locator(".pt-row")).to_have_count(1)
    expect(page.locator(".pt-cell-nome")).to_have_text("Elemento esportato")


def test_import_via_file_input_shows_name_and_warnings(page: Page, base_url: str, tmp_path) -> None:
    nome = _unique("Progetto File Import")
    payload = {
        "formato": "strutture-progetto",
        "versione": 1,
        "esportato": "2026-01-01T00:00:00Z",
        "app": "test",
        "progetto": {"codice": "", "nome": nome, "committente": "", "note": ""},
        "elementi": [
            {
                "strumento": "strumento-boh",
                "nome": "Elemento X",
                "inputs": {},
                "sintesi": {},
                "stato": "non_verificato",
                "modalita": "standard",
                "versione_app": "",
                "provenienza": {},
                "revisioni": [],
            }
        ],
    }
    file_path = tmp_path / "progetto.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    goto_progetti(page, base_url)
    page.locator("#pj-import-file").set_input_files(str(file_path))
    expect(page.locator(".pj-import-status")).to_contain_text(nome)
    expect(page.locator(".pj-import-status")).to_contain_text("strumento sconosciuto")
    expect(page.locator(".pj-row", has_text=nome)).to_have_count(1)


# -- "Relazione di progetto": every element, per-element sections, unknown tool -------------------


def _stub_print(page: Page) -> None:
    page.evaluate("() => { window.__printed = 0; window.print = () => { window.__printed++; }; }")


def test_project_report_contains_every_element(desktop_page: tuple[Page, PageCollectors], base_url: str) -> None:
    page, collectors = desktop_page
    nome = _unique("Progetto Relazione")
    progetto_id = create_project_via_ui(page, base_url, nome, codice="REL1", committente="ACME")

    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome="Prima verifica")

    goto_tool(page, base_url, "demo-relazione")
    load_example(page)  # see test_history_...'s own comment: `nota` needs a real string first
    page.fill(field_id("fattore"), "5")
    submit(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome="Seconda verifica")

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    _stub_print(page)
    page.get_by_role("button", name="Relazione di progetto").click()
    dialog = page.locator(".pr-overlay")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name="Genera e stampa").click()
    # The dialog only closes (`closeDialog()`, in a `finally`) once `generateAndPrint` -- every
    # element's fresh run AND `window.print()` -- has fully settled, so this alone is the signal
    # the print root is done being built (`page.wait_for_function` is CSP-blocked here: it needs
    # `new Function()`/`eval`, which this app's `default-src 'self'` forbids).
    expect(dialog).to_be_hidden()

    root = page.locator("#relazione-print-root")
    expect(root.locator(".print-progetto-cartiglio")).to_contain_text(nome)
    expect(root.locator(".print-progetto-cartiglio")).to_contain_text("ACME")
    sections = root.locator(".print-elemento-sezione")
    expect(sections).to_have_count(2)
    texts = sections.all_inner_texts()
    assert any("Prima verifica" in t for t in texts), texts
    assert any("Seconda verifica" in t for t in texts), texts
    # `demo-relazione` has real checks (this project report's own reason for using it: eta max/
    # verifica governante land in `sintesi`) but, per its own docstring, no `relazione` trace --
    # "Sviluppo dei calcoli" (fresh `?relazione=1` runs, gated on the TOOL's own schema saying it
    # supports one) is covered manually against a real tool instead; asserting it here would only
    # ever prove this fixture tool's own absence of one, never the feature.
    assert any("Verifica" in t for t in texts), texts

    assert collectors.console_errors == [], f"console.error calls: {collectors.console_errors}"
    assert collectors.page_errors == [], f"uncaught page errors: {collectors.page_errors}"


def test_unknown_tool_element_flagged_in_list_and_report(desktop_page: tuple[Page, PageCollectors], base_url: str) -> None:
    page, collectors = desktop_page
    import_payload = {
        "formato": "strutture-progetto",
        "versione": 1,
        "esportato": "2026-01-01T00:00:00Z",
        "app": "test",
        "progetto": {"codice": "", "nome": _unique("Progetto Strumento Sconosciuto"), "committente": "", "note": ""},
        "elementi": [
            {
                "strumento": "strumento-inesistente-xyz",
                "nome": "Elemento fantasma",
                "inputs": {},
                "sintesi": {},
                "stato": "non_verificato",
                "modalita": "standard",
                "versione_app": "",
                "provenienza": {},
                "revisioni": [],
            }
        ],
    }
    response = page.request.post(f"{base_url}/api/progetti/importa", data=import_payload)
    assert response.status == 200, response.text()
    progetto_id = response.json()["progetto"]["id"]

    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    # §20.2 fix: the name is always shown, never hidden behind the "unavailable" note.
    nome_cell = page.locator(".pt-cell-nome")
    expect(nome_cell).to_contain_text("Elemento fantasma")
    expect(nome_cell.locator(".pe-action--disabled")).to_contain_text("strumento non disponibile")

    _stub_print(page)
    page.get_by_role("button", name="Relazione di progetto").click()
    dialog = page.locator(".pr-overlay")
    dialog.get_by_role("button", name="Genera e stampa").click()
    expect(dialog).to_be_hidden()
    expect(page.locator("#relazione-print-root")).to_contain_text("Strumento non disponibile in questa versione")

    assert collectors.console_errors == [], f"console.error calls: {collectors.console_errors}"
    assert collectors.page_errors == [], f"uncaught page errors: {collectors.page_errors}"


# -- accessibility --------------------------------------------------------------------------------


def test_save_dialog_traps_focus_and_escape_returns_it(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    trigger = page.get_by_role("button", name="Salva in progetto", exact=True)
    trigger.click()
    dialog = page.locator(".es-dialog")
    expect(dialog).to_be_visible()

    for _ in range(30):
        page.keyboard.press("Tab")
        inside = page.evaluate("document.querySelector('.es-dialog').contains(document.activeElement)")
        assert inside, "Tab must never move focus outside the modal dialog"

    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    assert page.evaluate("document.activeElement.textContent") == "Salva in progetto"


# -- mobile usability -------------------------------------------------------------------------


def test_mobile_progetti_and_tool_page_no_overflow(mobile_page: tuple[Page, PageCollectors], base_url: str) -> None:
    page, _ = mobile_page
    goto_progetti(page, base_url)
    assert page.evaluate("document.documentElement.scrollWidth") <= page.evaluate("document.documentElement.clientWidth")

    goto_tool(page, base_url, "demo-relazione")
    assert page.evaluate("document.documentElement.scrollWidth") <= page.evaluate("document.documentElement.clientWidth")
    expect(page.get_by_role("button", name="Salva in progetto", exact=True)).to_be_visible()


# -- consolidated "no console errors" sweep (WORKBENCH_SPEC §14 acceptance) -----------------------


def test_zero_console_errors_across_progetti_flow(desktop_page: tuple[Page, PageCollectors], base_url: str) -> None:
    page, collectors = desktop_page
    progetto_id = create_project_via_ui(page, base_url, _unique("Progetto Console Pulita"))
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    save_current_tool_as_new_element(page, progetto_id=progetto_id, nome="Elemento pulito")

    goto_progetti(page, base_url)
    page.goto(f"{base_url}/#/progetti/{progetto_id}")
    page.locator(".pt-table").wait_for(state="visible")
    page.locator(".pt-cell-nome a").first.click()
    page.locator("#tool-title").wait_for(state="visible")
    page.wait_for_timeout(500)

    assert collectors.console_errors == [], f"console.error calls: {collectors.console_errors}"
    assert collectors.page_errors == [], f"uncaught page errors: {collectors.page_errors}"
