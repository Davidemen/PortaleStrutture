""""Sviluppo dei calcoli" (docs/architecture-phase2.md §5, extends WORKBENCH_SPEC §10/§11):
AST JSON -> MathML rendering of a tool's `relazione`, the overlay option that gates it, and the
"trace unavailable" fallback sentence. `ca-taglio-non-armato` is the one adopting tool (§6 demo
adoption): its own example produces 3 `Traccia` / 10 `Passo` (verified against
`strutture.shared.tool.execute(TOOL, TOOL.example, con_relazione=True)` directly). `demo-relazione`
(tests/e2e/_demo_tool.py) declares no `relazione` at all -- the "a tool without formulas" case.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from strutture.shared.tool import AVVISO_RELAZIONE_MODALITA_EXCEL

from ._actions import field_id, goto_tool, load_example, submit

pytestmark = pytest.mark.e2e

OVERLAY = "#relazione-overlay"
PRINT_ROOT = "#relazione-print-root"
TRACCE_ATTESE = 3
PASSI_ATTESI = 10


def _stub_print(page: Page) -> None:
    page.evaluate("() => { window.__printed = 0; window.print = () => { window.__printed++; }; }")


def _open_overlay(page: Page) -> None:
    page.get_by_role("button", name="Stampa relazione").click()
    page.locator(OVERLAY).wait_for(state="visible")


def _print_from_overlay(page: Page) -> None:
    page.get_by_role("button", name="Stampa / Salva PDF").click()
    page.locator(f"{PRINT_ROOT} .print-cartiglio").wait_for(state="attached")


def _load_taglio(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "ca-taglio-non-armato")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")


def test_section_appears_with_the_expected_number_of_equation_groups(page: Page, base_url: str) -> None:
    _load_taglio(page, base_url)
    _stub_print(page)
    _open_overlay(page)
    _print_from_overlay(page)

    root = page.locator(PRINT_ROOT)
    expect(root.locator(".r-sviluppo > h2")).to_have_text("Sviluppo dei calcoli")
    assert root.locator(".r-traccia").count() == TRACCE_ATTESE, "expected one .r-traccia per Traccia"
    assert root.locator(".r-passo").count() == PASSI_ATTESI, "expected one .r-passo per Passo"


def test_a_fraction_renders_as_mfrac(page: Page, base_url: str) -> None:
    _load_taglio(page, base_url)
    _stub_print(page)
    _open_overlay(page)
    _print_from_overlay(page)

    assert page.evaluate("'MathMLElement' in window"), "headless Chromium is expected to support MathML Core"
    fractions = page.locator(f"{PRINT_ROOT} .r-passo math mfrac")
    assert fractions.count() >= 1, "at least one formula (e.g. f_cd = 0.85*f_ck/γ_c) has a division"


def test_substitution_line_shows_italian_decimals(page: Page, base_url: str) -> None:
    _load_taglio(page, base_url)
    _stub_print(page)
    _open_overlay(page)
    _print_from_overlay(page)

    # f_ck's own Traccia ("Materiali") is first; its substitution line is "= 0,83·35".
    sostituzione = page.locator(f"{PRINT_ROOT} .r-traccia").first.locator(".r-passo-riga--sostituzione math").first
    testo = sostituzione.get_attribute("aria-label")
    assert testo, "expected the MathML root to carry the plain-text accessible name"
    assert "," in testo, f"expected an Italian decimal comma in {testo!r}"
    assert "." not in testo, f"expected no decimal POINT in {testo!r}"


def test_display_factor_is_printed(page: Page, base_url: str) -> None:
    _load_taglio(page, base_url)
    _stub_print(page)
    _open_overlay(page)
    _print_from_overlay(page)

    # V_Rd,1/V_Rd,2 (Resistenza a taglio) carry `scala=0.001` (N -> kN): "...·10⁻³" (§3).
    formule = page.locator(f"{PRINT_ROOT} .r-traccia").last.locator(".r-passo-riga--formula math")
    testi = [formule.nth(i).get_attribute("aria-label") or "" for i in range(formule.count())]
    assert any("10⁻³" in testo for testo in testi), f"expected a '·10⁻³' display factor in one of {testi!r}"


def test_clause_is_present(page: Page, base_url: str) -> None:
    _load_taglio(page, base_url)
    _stub_print(page)
    _open_overlay(page)
    _print_from_overlay(page)

    clausole = page.locator(f"{PRINT_ROOT} .r-passo-clausola")
    assert clausole.count() >= 1
    testi = clausole.all_inner_texts()
    assert any("NTC2018" in testo for testo in testi), f"expected a norm clause among {testi!r}"


def test_check_step_shows_its_outcome_word(page: Page, base_url: str) -> None:
    _load_taglio(page, base_url)
    _stub_print(page)
    _open_overlay(page)
    _print_from_overlay(page)

    # rho_l (NTC2018 §4.1.2.3.5.1) is the ONE check this tool restates as a comparison step.
    esito = page.locator(f"{PRINT_ROOT} .r-passo-esito")
    expect(esito).to_have_count(1)
    expect(esito.locator(".r-passo-esito-word")).to_have_text("soddisfatta")
    assert esito.get_attribute("class").split() == ["r-passo-esito", "r-passo-esito--ok"]


def test_the_option_toggles_the_section_off(page: Page, base_url: str) -> None:
    _load_taglio(page, base_url)
    _stub_print(page)
    _open_overlay(page)

    checkbox = page.locator("#rel-sezione-sviluppo")
    expect(checkbox).to_be_checked()
    page.wait_for_timeout(400)  # debounced preview: confirm it starts ON before toggling
    assert page.locator(".rel-page-content .r-traccia").count() > 0

    checkbox.uncheck()
    page.wait_for_timeout(400)
    assert page.locator(".rel-page-content .r-sviluppo").count() == 0
    expect(page.locator(".rel-page-content .print-omessi")).to_contain_text("Sviluppo dei calcoli")

    _print_from_overlay(page)
    root = page.locator(PRINT_ROOT)
    assert root.locator(".r-sviluppo").count() == 0
    expect(root.locator(".print-omessi")).to_contain_text("Sviluppo dei calcoli")


def test_a_tool_without_formulas_shows_neither_option_nor_section(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-relazione")
    load_example(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    _stub_print(page)
    _open_overlay(page)

    assert page.locator("#rel-sezione-sviluppo").count() == 0

    _print_from_overlay(page)
    assert page.locator(f"{PRINT_ROOT} .r-sviluppo").count() == 0


def test_excel_mode_prints_the_unavailable_sentence(page: Page, base_url: str) -> None:
    _load_taglio(page, base_url)
    page.locator("#form-root .f-advanced > summary").click()  # legacy_compat lives in "Avanzate"
    page.check(field_id("legacy_compat"))
    submit(page)
    page.locator("#r-group-verifiche").wait_for(state="visible")
    _stub_print(page)
    _open_overlay(page)
    _print_from_overlay(page)

    root = page.locator(PRINT_ROOT)
    assert root.locator(".r-traccia").count() == 0
    expect(root.locator(".r-sviluppo-assente")).to_have_text(AVVISO_RELAZIONE_MODALITA_EXCEL)
