"""Editable dimensions in the Sintesi sketch (owner's request, 2026-09-22): a dimension whose text
matches a number field by symbol and unit is a keyboard-reachable button; activating it opens a
popover with one input, applying writes the Dati field through a native "input" event (so live
calculation, persistence and the redraw all follow the ordinary path)."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool, load_example

pytestmark = pytest.mark.e2e


def _open_tool_with_sketch(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "vento-cpe-rettangolare")
    load_example(page)
    page.locator("#sintesi .r-si-sketch svg").first.wait_for(state="attached")


def test_click_on_a_dimension_edits_the_field_and_redraws(page: Page, base_url: str) -> None:
    _open_tool_with_sketch(page, base_url)
    quota_b = page.locator('#sintesi .sk-quota-text[data-campo="b"]')
    expect(quota_b.first).to_be_visible()
    assert quota_b.count() == 2  # one per view (direction 1 horizontal, direction 2 vertical)
    expect(quota_b.first).to_have_attribute("role", "button")
    expect(quota_b.first).to_have_attribute("tabindex", "0")
    assert page.locator('#sintesi .sk-quota-text[data-campo]').count() == 4  # b and d, twice

    quota_b.first.click()
    popover = page.locator("form.sk-edit")
    expect(popover).to_be_visible()
    expect(popover).to_have_attribute("aria-label", "Modifica b")
    field_input = popover.locator("#sk-edit-input")
    expect(field_input).to_be_focused()
    expect(field_input).to_have_value("15")
    field_input.fill("20")
    field_input.press("Enter")

    expect(popover).to_have_count(0)
    expect(page.locator('#tool-form [name="b"]')).to_have_value("20")
    expect(page.locator('#sintesi .sk-quota-text[data-campo="b"] text').first).to_have_text("b = 20,00 m")


def test_keyboard_enter_opens_escape_closes_and_restores_focus(page: Page, base_url: str) -> None:
    _open_tool_with_sketch(page, base_url)
    quota_d = page.locator('#sintesi .sk-quota-text[data-campo="d"]').first
    quota_d.focus()
    expect(quota_d).to_be_focused()
    page.keyboard.press("Enter")
    popover = page.locator("form.sk-edit")
    expect(popover).to_be_visible()
    page.keyboard.press("Escape")
    expect(popover).to_have_count(0)
    expect(quota_d).to_be_focused()
    expect(page.locator('#tool-form [name="d"]')).to_have_value("12")  # untouched


def test_non_numeric_input_is_refused_in_place(page: Page, base_url: str) -> None:
    _open_tool_with_sketch(page, base_url)
    page.locator('#sintesi .sk-quota-text[data-campo="b"]').first.click()
    popover = page.locator("form.sk-edit")
    popover.locator("#sk-edit-input").fill("abc")
    popover.locator("#sk-edit-input").press("Enter")
    expect(popover).to_be_visible()
    expect(popover.locator(".sk-edit-error")).to_have_text("Inserire un numero")
    expect(page.locator('#tool-form [name="b"]')).to_have_value("15")


def test_printed_relazione_sketch_is_not_editable(page: Page, base_url: str) -> None:
    """The relazione re-renders the sketch without the Dati fields: nothing to edit on paper."""
    _open_tool_with_sketch(page, base_url)
    page.add_init_script("window.print = () => {}")
    page.get_by_role("button", name="Stampa relazione", exact=True).first.click()
    overlay = page.locator(".rel-overlay-body")
    overlay.wait_for(state="visible")
    expect(overlay.locator(".sk-quota-text").first).to_be_attached()  # the sketch IS in the relazione
    assert overlay.locator(".sk-quota-text[data-campo]").count() == 0  # but nothing is editable there


@pytest.mark.parametrize(("tool", "campo"), [
    ("geo-cedimento-edometrico", "b"),  # the field has no unit hint: the sketch names it (`Quota.campo`)
    ("fond-trave-collegamento", "b_mm"),  # sketch in m, field in mm: only `Quota.campo` can link them
    ("fond-plinto-isolato", "ax_m"),  # inferred from symbol + unit
])
def test_dimensions_linked_by_symbol_or_by_campo(page: Page, base_url: str, tool: str, campo: str) -> None:
    goto_tool(page, base_url, tool)
    load_example(page)
    page.locator("#sintesi .r-si-sketch svg").first.wait_for(state="attached")
    expect(page.locator(f'#sintesi .sk-quota-text[data-campo="{campo}"]').first).to_be_attached()
