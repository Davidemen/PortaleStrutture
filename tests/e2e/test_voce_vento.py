"""Voce Vento in una sola schermata (WORKBENCH_SPEC §27.8, issue #16).

Same acceptance as the Neve pilot (tests/e2e/test_voce_neve.py): with the example, the numbers of
the entry screen are identical to those of the two single tools. `voce_vento_riferimento.json` was
captured from the single-tool pages BEFORE the entry existed.
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

RIFERIMENTO = json.loads((Path(__file__).parent / "voce_vento_riferimento.json").read_text(encoding="utf-8"))
NUM = re.compile(r"-?\d+(?:[.,]\d+)?")
VOCE = "#/voce/carichi/vento"
PRESSIONE = "vento-pressione"
CPE = "vento-cpe-rettangolare"


def _is_run(tool: str):
    return lambda r: r.request.method == "POST" and r.url.split("?")[0].endswith(f"/api/tools/{tool}/run")


def _goto(page: Page, base_url: str, route: str) -> None:
    page.goto(f"{base_url}/{route}")
    page.locator("#form-root .f-field").first.wait_for(state="visible")


def _casella(page: Page):
    return page.get_by_role("checkbox", name="Coefficienti Cpe", exact=True)


def _scheda(page: Page, nome: str):
    return page.locator("#voce-schede").get_by_role("tab", name=nome, exact=True)


def _assert_identico(page: Page, base_url: str, tool: str, response) -> None:
    atteso = RIFERIMENTO[tool]
    assert response.request.post_data_json == atteso["payload"]
    singolo = page.request.post(f"{base_url}/api/tools/{tool}/run", data=atteso["payload"])
    assert response.json()["data"] == singolo.json()["data"]
    assert response.json()["checks"] == singolo.json()["checks"]
    page.wait_for_timeout(300)  # the Sintesi paints right after results-rendered
    assert NUM.findall(page.locator("#sintesi").inner_text()) == atteso["sintesi"]


def _prepara_cpe(page: Page, base_url: str) -> None:
    _goto(page, base_url, f"{VOCE}?parte={CPE}")
    with page.expect_response(_is_run(CPE)):
        load_example(page)
    _scheda(page, "Pressione").click()
    expect(_scheda(page, "Pressione")).to_have_attribute("aria-selected", "true")
    with page.expect_response(_is_run(PRESSIONE)):
        load_example(page)


def test_pressione_con_esempio_numeri_identici(page: Page, base_url: str) -> None:
    _goto(page, base_url, VOCE)
    expect(_casella(page)).not_to_be_checked()
    expect(page.locator("#voce-schede")).to_be_hidden()
    with page.expect_response(_is_run(PRESSIONE)) as info:
        load_example(page)
    _assert_identico(page, base_url, PRESSIONE, info.value)


def test_cpe_con_esempio_numeri_identici(page: Page, base_url: str) -> None:
    _goto(page, base_url, f"{VOCE}?parte={CPE}")
    expect(_casella(page)).to_be_checked()
    expect(_scheda(page, "Coefficienti Cpe")).to_have_attribute("aria-selected", "true")
    with page.expect_response(_is_run(CPE)) as info:
        load_example(page)
    _assert_identico(page, base_url, CPE, info.value)


def test_casella_spuntata_non_cambia_i_numeri_della_pressione(page: Page, base_url: str) -> None:
    _prepara_cpe(page, base_url)
    with page.expect_response(_is_run(PRESSIONE)) as info:
        load_example(page)
    _assert_identico(page, base_url, PRESSIONE, info.value)
    # §27.8: no common data in Vento -- no chip, and the Cpe part shows all its own fields
    expect(page.locator(".vo-comune")).to_have_count(0)
    for nome in ("b", "d", "h"):
        expect(page.locator(f"#voce-compagno .f-field[data-field='vo__{nome}']")).to_have_count(1)


def test_vecchio_indirizzo_porta_alla_voce(page: Page, base_url: str) -> None:
    _goto(page, base_url, f"#/{CPE}?h=11")
    expect(page).to_have_url(re.compile(r"#/voce/carichi/vento\?parte=vento-cpe-rettangolare&h=11$"))
    expect(_casella(page)).to_be_checked()
    expect(page.locator(field_id("h"))).to_have_value("11")


def test_barra_e_ricerca_mostrano_la_voce_una_volta(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/#/")
    page.evaluate(f"localStorage.setItem('sm.nav.fav', JSON.stringify(['{CPE}', '{PRESSIONE}']))")
    page.reload()
    home = page.locator("#home-pane")
    preferiti = home.locator(".home-section", has=page.get_by_role("heading", name="Preferiti"))
    expect(preferiti.locator(".home-card-title")).to_have_text(["Vento"])
    expect(home.locator(".home-card-title", has_text="Coefficienti Cpe")).to_have_count(0)
    page.keyboard.press("Control+k")
    page.keyboard.type("Coefficienti Cpe vento")
    expect(page.locator(".palette-option-title").first).to_have_text("Vento")
    page.keyboard.press("Enter")
    expect(page).to_have_url(re.compile(r"#/voce/carichi/vento"))


def test_salva_con_cpe_crea_due_elementi(page: Page, base_url: str) -> None:
    risposta = page.request.post(f"{base_url}/api/progetti", data={"nome": f"Vento voce {time.time_ns()}"})
    progetto_id = risposta.json()["id"]
    _prepara_cpe(page, base_url)
    page.get_by_role("button", name="Salva in progetto", exact=True).click()
    dialog = page.locator(".es-dialog")
    dialog.locator("#es-dialog-progetto").select_option(progetto_id)
    dialog.locator("#es-dialog-nome").fill("Capannone")
    dialog.get_by_role("button", name="Salva", exact=True).click()
    expect(dialog).to_be_hidden()
    for _ in range(40):
        elementi = page.request.get(f"{base_url}/api/progetti/{progetto_id}/elementi").json()
        if len(elementi) == 2:
            break
        page.wait_for_timeout(100)
    per_nome = {e["nome"]: e for e in elementi}
    assert per_nome["Capannone -1"]["strumento"] == PRESSIONE
    assert per_nome["Capannone -2"]["strumento"] == CPE
    assert per_nome["Capannone -2"]["inputs"] == RIFERIMENTO[CPE]["payload"]
