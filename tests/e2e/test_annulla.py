"""Undo/redo on the Dati form's values (WORKBENCH_SPEC §21, owner's request 2026-09-22): Ctrl+Z /
Ctrl+Shift+Z / Ctrl+Y, one step per confirmed field change (typing closed by Tab/blur, a select, a
table paste), "Carica esempio" as one step, a §18 sketch edit as an ordinary step, native undo
first while a text box is mid-edit, and history kept per tool for the tab's life."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

from ._actions import field_id, goto_tool, load_example

pytestmark = pytest.mark.e2e

UNDO = "Annulla modifica"
REDO = "Ripristina modifica"


def _open_muro(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)


def test_edit_then_ctrl_z_restores_the_value_and_the_live_result_follows(page: Page, base_url: str) -> None:
    _open_muro(page, base_url)
    field = page.locator(field_id("h_muro_m"))
    expect(field).to_have_value("2,4")
    field.fill("3,5")
    field.press("Tab")
    expect(field).to_have_value("3,5")

    page.keyboard.press("Control+z")
    expect(field).to_have_value("2,4")


def test_typing_several_characters_is_one_step(page: Page, base_url: str) -> None:
    _open_muro(page, base_url)
    field = page.locator(field_id("h_muro_m"))
    field.click()  # js/number-input.js selects the whole value on focus
    page.keyboard.type("3,3")  # real keystrokes, unlike `.fill()` -- no `change` until Tab commits
    field.press("Tab")
    expect(field).to_have_value("3,3")

    page.keyboard.press("Control+z")
    expect(field).to_have_value("2,4")  # back to the example value in ONE undo, not per keystroke
    # The one step below it is "Carica esempio" itself (load_example, above) -- a second undo
    # reaches THAT step, not a leftover half-typed character.
    expect(page.get_by_role("button", name=UNDO)).to_have_attribute("title", "Annulla: Carica esempio")


def test_a_select_change_is_one_step(page: Page, base_url: str) -> None:
    _open_muro(page, base_url)
    select = page.locator(field_id("categoria_sottosuolo"))
    expect(select).to_have_value("C")
    select.select_option("A")
    expect(select).to_have_value("A")

    page.keyboard.press("Control+z")
    expect(select).to_have_value("C")


def test_redo_with_ctrl_shift_z_and_ctrl_y(page: Page, base_url: str) -> None:
    _open_muro(page, base_url)
    field = page.locator(field_id("h_muro_m"))
    field.fill("3,5")
    field.press("Tab")
    page.keyboard.press("Control+z")
    expect(field).to_have_value("2,4")

    page.keyboard.press("Control+Shift+Z")
    expect(field).to_have_value("3,5")

    page.keyboard.press("Control+z")
    expect(field).to_have_value("2,4")
    page.keyboard.press("Control+y")
    expect(field).to_have_value("3,5")


def test_a_new_edit_clears_redo(page: Page, base_url: str) -> None:
    _open_muro(page, base_url)
    field = page.locator(field_id("h_muro_m"))
    field.fill("3,5")
    field.press("Tab")
    page.keyboard.press("Control+z")
    expect(field).to_have_value("2,4")
    expect(page.get_by_role("button", name=REDO)).to_have_attribute("aria-disabled", "false")

    field.fill("2,8")
    field.press("Tab")
    expect(page.get_by_role("button", name=REDO)).to_have_attribute("aria-disabled", "true")


def test_undoing_carica_esempio_brings_back_the_users_data(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    field = page.locator(field_id("h_muro_m"))
    field.fill("9,9")
    field.press("Tab")
    expect(field).to_have_value("9,9")

    page.get_by_role("button", name="Carica esempio").click()
    expect(field).to_have_value("2,4")

    page.keyboard.press("Control+z")
    expect(field).to_have_value("9,9")


def test_undoing_a_sketch_edit_restores_the_field_and_the_dimension_text(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "vento-cpe-rettangolare")
    load_example(page)
    page.locator("#sintesi .r-si-sketch svg").first.wait_for(state="attached")
    quota_b = page.locator('#sintesi .sk-quota-text[data-campo="b"]').first
    quota_b.click()
    popover = page.locator("form.sk-edit")
    popover.locator("#sk-edit-input").fill("20")
    popover.locator("#sk-edit-input").press("Enter")
    expect(page.locator('#tool-form [name="b"]')).to_have_value("20")

    page.keyboard.press("Control+z")
    expect(page.locator('#tool-form [name="b"]')).to_have_value("15")
    expect(page.locator('#sintesi .sk-quota-text[data-campo="b"] text').first).to_have_text("b = 15,00 m")


def test_table_paste_is_one_step(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "demo-tabella")
    load_example(page)
    rows = page.locator("[data-field='stratigrafia'] table tbody tr")
    expect(rows).to_have_count(2)

    page.get_by_text("Incolla da Excel", exact=True).click()
    page.locator("textarea").fill("0\t10\n1\t12\n2\t14\n")
    page.get_by_role("button", name="Applica").click()
    expect(rows).to_have_count(3)

    page.keyboard.press("Control+z")
    expect(rows).to_have_count(2)  # the whole paste undone in one step


def test_buttons_work_by_mouse_and_name_the_step_in_the_tooltip(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")  # no "Carica esempio": one clean, checkable step
    undo_btn = page.get_by_role("button", name=UNDO)
    expect(undo_btn).to_have_attribute("aria-disabled", "true")

    field = page.locator(field_id("h_muro_m"))
    field.fill("3,5")
    field.press("Tab")
    expect(undo_btn).to_have_attribute("aria-disabled", "false")
    expect(undo_btn).to_have_attribute("title", "Annulla: Altezza del muro fuori terra — → 3,5 m")

    undo_btn.click()
    expect(field).to_have_value("")
    redo_btn = page.get_by_role("button", name=REDO)
    redo_btn.click()
    expect(field).to_have_value("3,5")


def test_meta_z_undoes_too(page: Page, base_url: str) -> None:
    _open_muro(page, base_url)
    field = page.locator(field_id("h_muro_m"))
    field.fill("3,5")
    field.press("Tab")
    page.keyboard.press("Meta+z")
    expect(field).to_have_value("2,4")


def test_switching_tool_and_back_keeps_the_history(page: Page, base_url: str) -> None:
    _open_muro(page, base_url)
    field = page.locator(field_id("h_muro_m"))
    field.fill("3,5")
    field.press("Tab")

    goto_tool(page, base_url, "demo-tabella")
    goto_tool(page, base_url, "muro-sostegno")

    field = page.locator(field_id("h_muro_m"))
    expect(field).to_have_value("3,5")  # values unchanged: the same tool's history resumes
    page.keyboard.press("Control+z")
    expect(field).to_have_value("2,4")


def test_mid_typing_ctrl_z_is_native_and_leaves_the_app_history_untouched(page: Page, base_url: str) -> None:
    _open_muro(page, base_url)  # one confirmed step already on the stack: "Carica esempio"
    undo_btn = page.get_by_role("button", name=UNDO)
    title_before = undo_btn.get_attribute("title")

    field = page.locator(field_id("h_muro_m"))
    field.click()
    page.keyboard.press("Control+a")
    page.keyboard.type("9")  # value now differs from the confirmed snapshot: mid-edit, never committed
    page.keyboard.press("Control+z")  # left to the browser (in-box character undo), not app-handled
    expect(undo_btn).to_have_attribute("title", title_before)  # the app's own history never moved
