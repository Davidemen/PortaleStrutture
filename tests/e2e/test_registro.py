"""E2E coverage for WORKBENCH_SPEC.md §13.1/§13.2: the `#/registro` divergence register page, the
rail's own pending-count destination, and the per-tool "N correzioni da confermare" indicator +
"respinta" banner. The e2e server (tests/e2e/_server.py) always uses a fresh `InMemorySignoffRepository`
and the REAL, packaged register (`strutture.shared.divergences.load_register()`, read-only JSON
files under src/strutture/data/) -- every entry starts `da_confermare`. Tests pick their OWN,
never-reused divergence ids so they stay independent of each other and of `test_rail_and_clipboard.py`.
"""
from __future__ import annotations

import re
from urllib.parse import quote

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

ARMATURA_ID = "muro-sostegno/armatura-necessaria-senza-limite-inferiore"  # ramo="nessuno"
COEFFICIENTI_ID = "muro-sostegno/coefficienti-resistenza-mancanti"  # ramo="codice"
DIAMETRO_ID = "muro-sostegno/diametro-armatura-non-commerciale"
FYK_ID = "muro-sostegno/fyk-input-libero-invece-di-classe"
GAMMA_ID = "muro-sostegno/gamma-e-unita-ambigua"
INERZIA_ID = "muro-sostegno/inerzia-sismica-muro-terreno-assente"
CONDIVISO_WITH_LINK_ID = "ca-pilastri/lambda-lim-ntc2018-foglio-non-normativo"  # ramo="condiviso", riprodotta_da non vuoto
CONDIVISO_LINK_TARGET_ID = "ca-pilastri/lambda-lim-manca-conversione-kn"
CONDIVISO_NO_LINK_ID = "ca-pilastri/controllo-percentuale-minima-rimosso-ntc2018-ec2"  # ramo="condiviso", riprodotta_da vuoto


def goto_registro(page: Page, base_url: str, query: str = "") -> None:
    page.goto(f"{base_url}/#/registro{query}")
    page.locator("#registro-pane h2").wait_for(state="visible")


def row_for(page: Page, divergence_id: str):
    return page.locator(f'.reg-row[data-id="{divergence_id}"]')


# -- rail entry ---------------------------------------------------------------------------------


def test_rail_has_registro_destination_with_pending_badge(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/#/muro-sostegno")
    page.locator("#tool-title").wait_for(state="visible")
    item = page.locator("#tool-index .rail-item", has_text="Registro correzioni")
    expect(item).to_have_count(1)
    # expanded rail (desktop): the count closes the row and the corner badge is hidden, so the
    # pictogram that identifies the entry stays uncovered; collapsed: the other way round
    count = item.locator(".rail-pending-count")
    expect(count).to_be_visible()
    expect(item.locator(".rail-pending-badge")).to_be_hidden()
    assert int(count.inner_text()) > 0, "the packaged register has da_confermare entries: the count must not be hidden"
    page.locator("#app").evaluate("app => app.classList.add('rail-collapsed')")
    expect(item.locator(".rail-pending-badge")).to_be_visible()
    expect(count).to_be_hidden()


def test_rail_registro_navigates_and_marks_current(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/#/muro-sostegno")
    page.locator("#tool-title").wait_for(state="visible")
    page.locator("#tool-index .rail-item", has_text="Registro correzioni").click()
    page.locator("#registro-pane h2").wait_for(state="visible")
    assert "#/registro" in page.url
    expect(page.locator("#tool-index .rail-item", has_text="Registro correzioni")).to_have_attribute("aria-current", "true")


# -- page: totals, grouping, filters -------------------------------------------------------------


def test_page_title_and_totals_strip(page: Page, base_url: str) -> None:
    goto_registro(page, base_url)
    expect(page.locator("#registro-pane h2")).to_have_text("Registro correzioni")
    buttons = page.locator(".reg-total-btn")
    expect(buttons).to_have_count(3)
    texts = buttons.all_inner_texts()
    assert texts[0].startswith("Da confermare ")
    assert texts[1].startswith("Approvate ")
    assert texts[2].startswith("Respinte ")
    for button in buttons.all():
        expect(button).to_have_attribute("aria-pressed", "false")


def test_state_filter_button_toggles_aria_pressed_and_hash(page: Page, base_url: str) -> None:
    goto_registro(page, base_url)
    button = page.locator(".reg-total-btn", has_text="Da confermare")
    button.click()
    expect(button).to_have_attribute("aria-pressed", "true")
    expect(page).to_have_url(re.compile(r"stato=da_confermare"))
    button.click()
    expect(button).to_have_attribute("aria-pressed", "false")


def test_grouped_list_shows_state_mark_title_tipo_and_sigla_chip(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, "?strumento=muro-sostegno")
    row = row_for(page, COEFFICIENTI_ID)
    expect(row).to_have_count(1)
    expect(row.locator(".reg-state")).to_have_text("○ Da confermare")
    expect(row.locator(".reg-row-tipo")).to_have_text("Errore del foglio")
    expect(row.locator(".reg-tool-link")).to_have_count(1)
    expect(row.locator(".reg-tool-link .sm-sigla-chip")).to_have_text("MUR")
    heading = page.locator(".reg-group-heading", has_text="Muro sostegno")
    expect(heading).to_have_count(1)


def test_search_filters_the_list(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, "?strumento=muro-sostegno")
    expect(row_for(page, COEFFICIENTI_ID)).to_have_count(1)
    page.locator("#reg-search").fill("coefficienti di resistenza")
    page.wait_for_timeout(400)  # 250ms debounce
    expect(page).to_have_url(re.compile(r"q="))
    expect(row_for(page, COEFFICIENTI_ID)).to_have_count(1)
    expect(row_for(page, DIAMETRO_ID)).to_have_count(0)


def test_tipo_filter_narrows_the_list(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, "?strumento=muro-sostegno")
    page.locator("#reg-tipo").select_option("scelta_ingegneristica")
    page.wait_for_timeout(300)
    expect(page).to_have_url(re.compile(r"tipo=scelta_ingegneristica"))
    expect(row_for(page, FYK_ID)).to_have_count(1)  # scelta_ingegneristica
    expect(row_for(page, COEFFICIENTI_ID)).to_have_count(0)  # errore_foglio


# -- expand / sign-off ----------------------------------------------------------------------------


def test_expand_row_shows_foglio_strumento_and_form(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, f"?id={quote(COEFFICIENTI_ID, safe='')}")
    row = row_for(page, COEFFICIENTI_ID)
    toggle = row.locator(".reg-row-toggle")
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(row.locator(".reg-compare-col")).to_have_count(2)
    expect(row.locator(".reg-form")).to_have_count(1)
    expect(row.locator(".reg-history")).to_have_count(1)
    # collapsing again works
    toggle.click()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(row.locator(".reg-row-body")).to_be_hidden()


def test_ramo_codice_shows_riprodotta_message(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, f"?id={quote(COEFFICIENTI_ID, safe='')}")
    row = row_for(page, COEFFICIENTI_ID)
    line = row.locator(".reg-excel-mode")
    expect(line).to_have_count(1)
    expect(line).to_have_text("Riprodotta in modalità Excel")


def test_ramo_condiviso_with_riprodotta_da_links_and_shows_motivo(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, f"?id={quote(CONDIVISO_WITH_LINK_ID, safe='')}")
    row = row_for(page, CONDIVISO_WITH_LINK_ID)
    wrap = row.locator(".reg-excel-mode-wrap")
    expect(wrap).to_have_count(1)
    line = wrap.locator(".reg-excel-mode")
    expect(line).to_contain_text("Riprodotta in modalità Excel insieme a")
    link = line.locator("a")
    expect(link).to_have_count(1)
    expect(link).to_have_text(CONDIVISO_LINK_TARGET_ID)
    assert link.get_attribute("href") == f"#/registro?id={quote(CONDIVISO_LINK_TARGET_ID, safe='')}"
    note = wrap.locator(".reg-excel-mode-note")
    expect(note).to_be_visible()
    assert note.inner_text().strip() != ""


def test_ramo_condiviso_without_riprodotta_da_omits_links(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, f"?id={quote(CONDIVISO_NO_LINK_ID, safe='')}")
    row = row_for(page, CONDIVISO_NO_LINK_ID)
    line = row.locator(".reg-excel-mode-wrap .reg-excel-mode")
    expect(line).to_have_text("Riprodotta in modalità Excel")
    expect(line.locator("a")).to_have_count(0)
    expect(row.locator(".reg-excel-mode-note")).to_be_visible()


def test_ramo_nessuno_shows_non_riprodotta_warning(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, f"?id={quote(ARMATURA_ID, safe='')}")
    row = row_for(page, ARMATURA_ID)
    line = row.locator(".reg-excel-mode--none")
    expect(line).to_have_count(1)
    expect(line).to_contain_text("NON riprodotta in modalità Excel")
    expect(line.locator(".reg-excel-mode-icon")).to_have_count(1)


def test_excel_chip_filters_to_ramo_nessuno_and_reflects_in_hash(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, "?strumento=muro-sostegno")
    expect(row_for(page, ARMATURA_ID)).to_have_count(1)  # ramo="nessuno"
    expect(row_for(page, COEFFICIENTI_ID)).to_have_count(1)  # ramo="codice"

    chip = page.locator(".reg-excel-chip")
    expect(chip).to_have_attribute("aria-pressed", "false")
    chip.click()
    expect(chip).to_have_attribute("aria-pressed", "true")
    expect(page).to_have_url(re.compile(r"excel=no"))
    expect(row_for(page, ARMATURA_ID)).to_have_count(1)
    expect(row_for(page, COEFFICIENTI_ID)).to_have_count(0)

    chip.click()
    expect(chip).to_have_attribute("aria-pressed", "false")
    expect(row_for(page, COEFFICIENTI_ID)).to_have_count(1)


def test_signoff_requires_sigla_unless_da_confermare(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, f"?id={quote(DIAMETRO_ID, safe='')}")
    row = row_for(page, DIAMETRO_ID)
    form = row.locator(".reg-form")
    form.locator('input[type="radio"][value="approvato"]').check()
    form.locator(".reg-form-save").click()
    error = form.locator(".reg-form-error")
    expect(error).to_be_visible()
    expect(error).to_contain_text("sigla")
    # the row must NOT have updated -- still da_confermare
    expect(row.locator(".reg-state")).to_have_text("○ Da confermare")


def test_signoff_updates_row_only_after_server_confirms(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, f"?id={quote(GAMMA_ID, safe='')}")
    row = row_for(page, GAMMA_ID)
    before = page.locator(".reg-total-btn", has_text="Respinte").inner_text()
    before_count = int(before.split()[-1])

    form = row.locator(".reg-form")
    form.locator('input[type="radio"][value="respinto"]').check()
    form.locator('input[type="text"]').first.fill("AB")
    status = form.locator(".reg-form-status")
    expect(status).to_be_empty()
    form.locator(".reg-form-save").click()

    expect(status).to_have_text("Decisione salvata.")
    expect(row.locator(".reg-state")).to_have_text("✕ Respinta")
    expect(row.locator(".reg-last-decision")).to_contain_text("AB")
    after = page.locator(".reg-total-btn", has_text="Respinte").inner_text()
    assert int(after.split()[-1]) == before_count + 1


def test_bulk_signoff(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, "?strumento=muro-sostegno")
    row_a = row_for(page, INERZIA_ID)
    row_b = row_for(page, "muro-sostegno/momento-paramento-altezza-piena-invece-di-stelo")
    row_a.locator(".reg-row-check").check()
    row_b.locator(".reg-row-check").check()

    bulk_button = page.locator(".reg-bulk-btn")
    expect(bulk_button).to_have_text("Decidi per le 2 selezionate…")
    bulk_button.click()
    panel = page.locator(".reg-bulk-panel")
    expect(panel).to_be_visible()
    panel.locator('input[type="radio"][value="approvato"]').check()
    panel.locator('input[type="text"]').first.fill("CD")
    panel.locator(".reg-form-save").click()
    expect(panel.locator(".reg-form-status")).to_have_text("Decisione salvata.")

    expect(row_a.locator(".reg-state")).to_have_text("✓ Approvata")
    expect(row_b.locator(".reg-state")).to_have_text("✓ Approvata")


# -- per-tool indicator + respinta banner (WORKBENCH_SPEC §13.2) --------------------------------


def test_per_tool_indicator_link_and_respinta_banner(page: Page, base_url: str) -> None:
    # ca-punzonamento's own divergences are self-contained (not shared with any other tool), so
    # rejecting one here cannot affect another test's counts.
    goto_registro(page, base_url, "?strumento=ca-punzonamento")
    first_row = page.locator(".reg-list .reg-row").first
    first_row.locator(".reg-row-toggle").click()
    form = first_row.locator(".reg-form")
    form.locator('input[type="radio"][value="respinto"]').check()
    form.locator('input[type="text"]').first.fill("EF")
    form.locator(".reg-form-save").click()
    expect(form.locator(".reg-form-status")).to_have_text("Decisione salvata.")

    page.goto(f"{base_url}/#/ca-punzonamento")
    page.locator("#tool-title").wait_for(state="visible")
    indicator = page.locator("#tool-registro-indicator")
    link = indicator.locator(".reg-indicator-link--warn")
    expect(link).to_be_visible()
    expect(link).to_contain_text("correzion")
    expect(link).to_contain_text("da confermare")
    assert "strumento=ca-punzonamento" in link.get_attribute("href")
    assert "stato=da_confermare" in link.get_attribute("href")

    banner = page.locator(".reg-banner")
    expect(banner).to_be_visible()
    expect(banner).to_contain_text("respinta")
    banner_link = banner.locator("a")
    expect(banner_link).to_have_text("Apri il registro.")
    assert "stato=respinto" in banner_link.get_attribute("href")

    # follow the banner link back into the filtered register
    banner_link.click()
    page.locator("#registro-pane h2").wait_for(state="visible")
    expect(page.locator(".reg-total-btn", has_text="Respinte")).to_have_attribute("aria-pressed", "true")


# -- keyboard / a11y ------------------------------------------------------------------------------


def test_row_toggle_is_keyboard_operable_with_visible_focus(page: Page, base_url: str) -> None:
    goto_registro(page, base_url, "?strumento=muro-sostegno")
    row = row_for(page, "muro-sostegno/st-input-libero-invece-di-enum")
    toggle = row.locator(".reg-row-toggle")
    toggle.focus()
    outline = page.evaluate("getComputedStyle(document.activeElement).outlineWidth")
    assert outline != "0px", "the row toggle must have a visible :focus-visible outline"
    page.keyboard.press("Enter")
    expect(toggle).to_have_attribute("aria-expanded", "true")


# -- mobile usability -------------------------------------------------------------------------


def test_mobile_registro_has_no_horizontal_overflow(mobile_page: tuple[Page, object], base_url: str) -> None:
    page, _ = mobile_page
    goto_registro(page, base_url, "?strumento=muro-sostegno")
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    client_width = page.evaluate("document.documentElement.clientWidth")
    assert scroll_width <= client_width, f"horizontal overflow at 390px: {scroll_width} > {client_width}"
    row = row_for(page, "muro-sostegno/verifica-portanza-non-segnalata")
    row.locator(".reg-row-toggle").click()
    expect(row.locator(".reg-form")).to_be_visible()
