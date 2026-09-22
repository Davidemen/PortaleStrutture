"""User feedback (2026-09-22): a warning that names a parameter jumps to it; the sticky summary no
longer flickers when a group is opened and the results are scrolled."""
import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool, load_example

pytestmark = pytest.mark.e2e


def test_a_warning_about_an_input_jumps_to_it(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "ca-trave-rettangolare")
    load_example(page)
    page.locator("#sintesi .r-si-verdict").wait_for(state="visible")
    # the beam example leaves V_g at 0: the tool warns and says which field (Report.avvisi_campi)
    page.locator("#form-root").get_by_role("button", name="Comprimi tutto").click()
    panel = page.locator("#r-warnings-panel")
    panel.evaluate("d => { d.open = true; }")
    jump = panel.locator("button.r-warning-jump", has_text="carichi gravitazionali")
    expect(jump).to_have_count(1)
    jump.click()
    field = page.locator("#field-v_gravita_kN")
    expect(field).to_be_focused()
    expanded = page.evaluate(
        """() => document.querySelector('.f-field[data-field="v_gravita_kN"]').closest('.f-section')
                 .querySelector('.f-section-toggle').getAttribute('aria-expanded')"""
    )
    assert expanded == "true"


def test_a_warning_without_a_field_stays_plain_text(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "acciaio-resistenza-incendio")
    load_example(page)
    page.locator("#sintesi .r-si-layout").wait_for(state="visible")
    panel = page.locator("#r-warnings-panel")
    expect(panel.locator("p")).not_to_have_count(0)
    expect(panel.locator("button.r-warning-jump")).to_have_count(0)


def test_sticky_summary_collapse_has_hysteresis_and_keeps_the_scroll_range(page: Page, base_url: str) -> None:
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    page.locator("#sintesi .r-si-sketch svg").first.wait_for(state="attached")
    page.locator("#results-root").get_by_role("button", name="Espandi tutto").click()
    pane = page.locator("#results-pane")
    scroll = lambda y: pane.evaluate("(p, y) => { p.scrollTop = y; p.dispatchEvent(new Event('scroll')); }", y)
    scroll(400)
    page.wait_for_timeout(100)
    assert "r-sintesi--collapsed" in page.locator("#sintesi").get_attribute("class")
    spacer = pane.evaluate("p => p.style.getPropertyValue('--sm-collapse-spacer')")
    assert spacer.endswith("px") and float(spacer[:-2]) > 0
    # the collapse must not have thrown the reader back up
    assert pane.evaluate("p => p.scrollTop") >= 350
    scroll(120)  # under the collapse threshold but not back at the top: stays collapsed (hysteresis)
    page.wait_for_timeout(100)
    assert "r-sintesi--collapsed" in page.locator("#sintesi").get_attribute("class")
    scroll(0)
    page.wait_for_timeout(100)
    assert "r-sintesi--collapsed" not in page.locator("#sintesi").get_attribute("class")
    assert pane.evaluate("p => p.style.getPropertyValue('--sm-collapse-spacer')") == "0px"
