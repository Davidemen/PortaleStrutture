"""Voce Neve in una sola schermata (WORKBENCH_SPEC §27, pilota; issue #11).

Criterio del titolare: con l'esempio, i numeri della schermata della voce sono identici a quelli
dei due strumenti singoli di oggi. `voce_neve_riferimento.json` è stato catturato dalla pagina del
singolo strumento PRIMA di introdurre la voce (payload inviato con "Carica esempio" e numeri della
Sintesi); il report di riferimento si ricalcola qui con `page.request` sullo stesso payload.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from ._actions import field_id, load_example

pytestmark = pytest.mark.e2e

RIFERIMENTO = json.loads((Path(__file__).parent / "voce_neve_riferimento.json").read_text(encoding="utf-8"))
NUM = re.compile(r"-?\d+(?:[.,]\d+)?")
VOCE = "#/voce/carichi/neve"
FALDA = "neve-carico-falda"
ACCUMULO = "neve-accumulo"
COMUNI = ["comune", "zona", "as_m", "ct", "topografia"]


def _is_run(tool: str):
    return lambda r: r.request.method == "POST" and r.url.split("?")[0].endswith(f"/api/tools/{tool}/run")


def _goto(page: Page, base_url: str, route: str) -> None:
    page.goto(f"{base_url}/{route}")
    page.locator("#form-root .f-field").first.wait_for(state="visible")


def _casella(page: Page):
    return page.get_by_role("checkbox", name="Accumulo", exact=True)


def _scheda(page: Page, nome: str):
    return page.locator("#voce-schede").get_by_role("tab", name=nome, exact=True)


def _numeri_sintesi(page: Page) -> list[str]:
    page.wait_for_timeout(300)  # the Sintesi paints right after results-rendered
    return NUM.findall(page.locator("#sintesi").inner_text())


def _assert_identico(page: Page, base_url: str, tool: str, response) -> None:
    atteso = RIFERIMENTO[tool]
    assert response.request.post_data_json == atteso["payload"]
    singolo = page.request.post(f"{base_url}/api/tools/{tool}/run", data=atteso["payload"])
    assert response.json()["data"] == singolo.json()["data"]
    assert response.json()["checks"] == singolo.json()["checks"]
    assert _numeri_sintesi(page) == atteso["sintesi"]


def _prepara_accumulo(page: Page, base_url: str) -> None:
    """The accumulo part needs its own data (b1, b2, h, …) before it can run: load its example on
    its own tab, then come back to Copertura -- the order an engineer would follow."""
    _goto(page, base_url, f"{VOCE}?parte={ACCUMULO}")
    with page.expect_response(_is_run(ACCUMULO)):
        load_example(page)
    _scheda(page, "Copertura").click()
    expect(_scheda(page, "Copertura")).to_have_attribute("aria-selected", "true")
    with page.expect_response(_is_run(FALDA)):
        load_example(page)


# -- numeri identici (§27.10) --------------------------------------------------------------------


def test_copertura_con_esempio_numeri_identici(page: Page, base_url: str) -> None:
    _goto(page, base_url, VOCE)
    expect(_casella(page)).not_to_be_checked()
    with page.expect_response(_is_run(FALDA)) as info:
        load_example(page)
    _assert_identico(page, base_url, FALDA, info.value)


def test_accumulo_con_esempio_numeri_identici(page: Page, base_url: str) -> None:
    _goto(page, base_url, f"{VOCE}?parte={ACCUMULO}")
    expect(_casella(page)).to_be_checked()
    expect(_scheda(page, "Accumulo")).to_have_attribute("aria-selected", "true")
    with page.expect_response(_is_run(ACCUMULO)) as info:
        load_example(page)
    _assert_identico(page, base_url, ACCUMULO, info.value)


def test_casella_spuntata_non_cambia_i_numeri_della_copertura(page: Page, base_url: str) -> None:
    _goto(page, base_url, VOCE)
    _casella(page).check()
    expect(page.locator("#voce-compagno")).to_be_visible()
    with page.expect_response(_is_run(FALDA)) as info:
        load_example(page)
    _assert_identico(page, base_url, FALDA, info.value)


# -- dati comuni (§27.4) -------------------------------------------------------------------------


def test_dati_comuni_hanno_il_chip_e_non_si_ripetono(page: Page, base_url: str) -> None:
    _goto(page, base_url, VOCE)
    _casella(page).check()
    for nome in COMUNI:
        expect(page.locator(f"#tool-form .f-field[data-field='{nome}'] .vo-comune")).to_have_count(1)
    expect(page.locator("#tool-form .vo-comune")).to_have_count(len(COMUNI))
    # `a` has the same name in both tools but a different meaning: never common, shown in both
    expect(page.locator("#tool-form .f-field[data-field='a'] .vo-comune")).to_have_count(0)
    compagno = page.locator("#voce-compagno")
    for nome in COMUNI:
        expect(compagno.locator(f".f-field[data-field='vo__{nome}']")).to_have_count(0)
    expect(compagno.locator(".f-field[data-field$='__a']")).to_have_count(1)


def test_quota_scritta_in_copertura_arriva_all_accumulo(page: Page, base_url: str) -> None:
    _prepara_accumulo(page, base_url)
    with page.expect_response(lambda r: _is_run(ACCUMULO)(r) and r.request.post_data_json.get("as_m") == 612) as info:
        page.fill(field_id("as_m"), "612")
    assert info.value.request.post_data_json["comune"] == "Mapello"
    _scheda(page, "Accumulo").click()
    expect(page.locator(field_id("as_m"))).to_have_value("612")


def test_stacca_e_ricollega(page: Page, base_url: str) -> None:
    _goto(page, base_url, VOCE)
    _casella(page).check()
    load_example(page)
    chip = page.locator("#tool-form .f-field[data-field='as_m'] .vo-comune")
    chip.locator("summary").click()
    chip.get_by_role("button", name="Stacca").click()
    # detached: the other part now shows its own copy of the field
    copia = page.locator("#voce-compagno .f-field[data-field$='__as_m'] input")
    expect(copia).to_be_visible()
    page.fill(field_id("as_m"), "700")
    page.wait_for_timeout(700)
    expect(copia).not_to_have_value("700")
    chip = page.locator("#tool-form .f-field[data-field='as_m'] .vo-comune")
    chip.locator("summary").click()
    chip.get_by_role("button", name="Ricollega").click()
    expect(copia).to_be_hidden()
    expect(page.locator(field_id("as_m"))).not_to_have_value("700")


# -- schede, tastiera, indirizzi (§27.3, §27.5) --------------------------------------------------


def test_schede_dei_risultati_da_tastiera(page: Page, base_url: str) -> None:
    _goto(page, base_url, VOCE)
    expect(page.locator("#voce-schede")).to_be_hidden()
    _casella(page).focus()
    page.keyboard.press("Space")
    expect(_casella(page)).to_be_checked()
    _scheda(page, "Copertura").focus()
    page.keyboard.press("ArrowRight")
    expect(_scheda(page, "Accumulo")).to_be_focused()
    page.keyboard.press("Enter")
    expect(_scheda(page, "Accumulo")).to_have_attribute("aria-selected", "true")
    expect(page).to_have_url(re.compile(r"#/voce/carichi/neve\?parte=neve-accumulo"))
    expect(page.locator("#voce-compagno-titolo")).to_have_text("Copertura: dati")


def test_vecchio_indirizzo_porta_alla_voce(page: Page, base_url: str) -> None:
    _goto(page, base_url, f"#/{ACCUMULO}?as_m=333")
    expect(page).to_have_url(re.compile(r"#/voce/carichi/neve\?parte=neve-accumulo&as_m=333$"))
    expect(_casella(page)).to_be_checked()
    expect(page.locator(field_id("as_m"))).to_have_value("333")
    page.go_back()
    expect(page).not_to_have_url(re.compile(ACCUMULO))


def test_barra_home_e_ricerca_mostrano_la_voce_una_volta(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/#/")
    page.evaluate(f"localStorage.setItem('sm.nav.fav', JSON.stringify(['{FALDA}', '{ACCUMULO}']))")
    page.reload()
    home = page.locator("#home-pane")
    preferiti = home.locator(".home-section", has=page.get_by_role("heading", name="Preferiti"))
    expect(preferiti.locator(".home-card")).to_have_count(1)
    expect(preferiti.locator(".home-card-title")).to_have_text("Neve")
    carichi = home.locator(".home-section", has=page.get_by_role("heading", name="Carichi"))
    expect(carichi.locator(".home-card-title", has_text=re.compile("^Neve$"))).to_have_count(1)
    expect(home.locator(".home-card-title", has_text="Accumulo neve")).to_have_count(0)
    expect(home.locator(".home-card-title", has_text="Carico neve su copertura")).to_have_count(0)
    # rail: the Carichi flyout lists the entry once
    page.locator(".rail-toggle").click()
    page.locator("#tool-index").get_by_role("button", name="Carichi", exact=True).click()
    flyout = page.locator(".rail-flyout")
    expect(flyout.locator(".rail-row-title", has_text=re.compile("^Neve$"))).to_have_count(1)
    expect(flyout.locator(".rail-row-title", has_text="Accumulo neve")).to_have_count(0)
    page.keyboard.press("Escape")
    # palette: found by the title of a part, listed as the entry
    page.keyboard.press("Control+k")
    page.keyboard.type("Accumulo neve su coperture")
    expect(page.locator(".palette-option-title").first).to_have_text("Neve")
    expect(page.locator(".palette-option-title", has_text="Accumulo neve")).to_have_count(0)
    page.keyboard.press("Enter")
    expect(page).to_have_url(re.compile(r"#/voce/carichi/neve"))


# -- progetti (§27.7) ----------------------------------------------------------------------------


def _nuovo_progetto(page: Page, base_url: str) -> str:
    response = page.request.post(f"{base_url}/api/progetti", data={"nome": f"Neve voce {time.time_ns()}"})
    assert response.status in (200, 201), response.text()
    return response.json()["id"]


def test_salva_con_accumulo_crea_due_elementi(page: Page, base_url: str) -> None:
    progetto_id = _nuovo_progetto(page, base_url)
    _prepara_accumulo(page, base_url)
    page.get_by_role("button", name="Salva in progetto", exact=True).click()
    dialog = page.locator(".es-dialog")
    dialog.locator("#es-dialog-progetto").select_option(progetto_id)
    dialog.locator("#es-dialog-nome").fill("Capannone")
    dialog.locator("#es-dialog-sigla").fill("N1")
    dialog.get_by_role("button", name="Salva", exact=True).click()
    expect(dialog).to_be_hidden()
    expect(page.locator(".es-state-text")).to_contain_text("Capannone -1")
    elementi = page.request.get(f"{base_url}/api/progetti/{progetto_id}/elementi").json()
    per_nome = {e["nome"]: e for e in elementi}
    assert per_nome["Capannone -1"]["strumento"] == FALDA
    assert per_nome["Capannone -2"]["strumento"] == ACCUMULO
    for elemento in per_nome.values():  # the sigla is who saved: the same on both revisions
        revisioni = page.request.get(f"{base_url}/api/elementi/{elemento['id']}/revisioni").json()
        assert revisioni[-1]["sigla"] == "N1"
    assert per_nome["Capannone -2"]["inputs"]["comune"] == "Mapello"
    # "Salva" afterwards updates both, each with its own revisione
    page.fill(field_id("as_m"), "400")
    page.get_by_role("button", name="Salva", exact=True).click()
    expect(page.locator(".es-status")).to_have_text("Elemento salvato.")
    for _ in range(40):  # the second element is updated right after the first one
        elementi = page.request.get(f"{base_url}/api/progetti/{progetto_id}/elementi").json()
        if all(e["revisione"] == 2 for e in elementi):
            break
        page.wait_for_timeout(100)
    for elemento in elementi:
        assert elemento["inputs"]["as_m"] == 400
        assert elemento["revisione"] == 2


def test_elemento_di_accumulo_si_riapre_sulla_sua_parte(page: Page, base_url: str) -> None:
    progetto_id = _nuovo_progetto(page, base_url)
    inputs = {**RIFERIMENTO[ACCUMULO]["payload"], "as_m": 321}
    body = {"strumento": ACCUMULO, "nome": "Accumulo salvato", "inputs": inputs, "sintesi": {}, "stato": "verificato", "modalita": "standard"}
    creato = page.request.post(f"{base_url}/api/progetti/{progetto_id}/elementi", data=body)
    assert creato.status in (200, 201), creato.text()
    _goto(page, base_url, f"#/{ACCUMULO}?elemento={creato.json()['id']}")
    expect(page).to_have_url(re.compile(r"#/voce/carichi/neve\?parte=neve-accumulo&elemento="))
    expect(_casella(page)).to_be_checked()
    expect(page.locator(field_id("as_m"))).to_have_value("321")
    expect(page.locator(".es-state-text")).to_contain_text("Accumulo salvato")


# -- telefono (§27.10) ---------------------------------------------------------------------------


def test_telefono_senza_scorrimento_orizzontale(mobile_page, base_url: str) -> None:
    page = mobile_page[0]
    page.goto(f"{base_url}/{VOCE}?parte={ACCUMULO}")
    expect(_casella(page)).to_be_checked()
    larghezza = page.evaluate("document.documentElement.scrollWidth")
    assert larghezza <= 390


# -- relazione (§27.6) ---------------------------------------------------------------------------


def test_relazione_stampa_solo_la_parte_visibile(page: Page, base_url: str) -> None:
    _prepara_accumulo(page, base_url)
    with page.expect_response(_is_run(ACCUMULO)):
        _scheda(page, "Accumulo").click()
    expect(page.locator("#sintesi")).not_to_be_empty()
    page.evaluate("() => { window.print = () => {}; }")
    page.get_by_role("button", name="Stampa relazione").click()
    page.locator("#relazione-overlay").wait_for(state="visible")
    page.get_by_role("button", name="Stampa / Salva PDF").click()
    documento = page.locator("#relazione-print-root")
    documento.locator(".print-cartiglio").wait_for(state="attached")
    testo = documento.inner_text()
    assert "Accumulo neve su coperture adiacenti" in testo
    assert "Carico neve su copertura (una/due falde)" not in testo
    assert "43,15" in testo  # b1 of the accumulo example, i.e. the visible part's own inputs
