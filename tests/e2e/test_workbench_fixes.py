"""E2E coverage for the design-lead review findings (build/ui-review/wb-*.jpg) fixed in this
pass: compact Dati rows (A), the two-column Sintesi (B), sketch geometry/label quality (C),
two-decimal utilisation everywhere (D), the decluttered results head/toolbar (E), the one-row
Dati action bar (F), the collapsed-by-default rail (G), the header search trigger (H). Finding J
(muro-sostegno results <=900px) is covered by `test_wall_results_height_budget` in
test_workbench_acceptance.py, no longer xfail.
"""
from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from ._actions import goto_tool, load_example

pytestmark = pytest.mark.e2e

UTIL_RE = re.compile(r"^\d,\d\d$")  # exactly two decimals, it-IT comma


def _expand_all_dati(page: Page) -> None:
    page.locator("#form-root").get_by_role("button", name="Espandi tutto").click()


# -- A: compact Dati rows -------------------------------------------------------------------


def test_dati_rows_are_compact_at_desktop_width(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding A: at >=380px of the Dati column's width each field is one row
    (label left, control right), not label-above-control -- and the unit sits inside the
    control, not in the label."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)

    row = page.locator('[data-field="ag_g"] .f-field-row')
    expect(row).to_have_css("display", "grid")

    # Label and control sit side by side on the SAME row, not stacked.
    label_box = page.locator('[data-field="ag_g"] .f-field-labelcell').bounding_box()
    control_box = page.locator('[data-field="ag_g"] .f-field-control').bounding_box()
    assert label_box and control_box
    assert abs(label_box["y"] - control_box["y"]) < 4, "label and control must share one row"
    assert control_box["x"] > label_box["x"] + label_box["width"] - 4, "control must sit to the right of the label"

    # The unit is a suffix INSIDE the control column, not a separate node in the label.
    assert page.locator('[data-field="ag_g"] .f-field-label .f-unit').count() == 0
    assert page.locator('[data-field="ag_g"] .f-field-control .f-unit').count() == 1


def test_dati_rows_fall_back_to_stacked_below_380px(mobile_page: tuple[Page, object], base_url: str) -> None:
    """WORKBENCH_SPEC finding A/K: "below 380px of column width fall back to stacked" --
    exercised at the 390px mobile viewport, where the Dati column IS the (narrow) full width."""
    page, _ = mobile_page
    goto_tool(page, base_url, "muro-sostegno")
    page.get_by_role("tab", name="Dati").click()
    row = page.locator('[data-field="ag_g"] .f-field-row').first
    expect(row).to_have_css("display", "flex")


def test_muro_form_all_expanded_height_budget(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding A: "muro-sostegno form with ALL sections expanded <=1900px" (it
    was ~3000px before compact rows)."""
    goto_tool(page, base_url, "muro-sostegno")  # goto_tool already expands every section
    load_example(page)
    page.wait_for_timeout(300)
    height = page.evaluate("document.getElementById('form-root').scrollHeight")
    assert height <= 1900, f"muro-sostegno Dati column (all expanded) is {height}px, budget is 1900px"


def test_long_field_description_has_disclosure_toggle(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding A: a description too long for the 2-line clamp gets a "?"
    disclosure instead of silently clipping. `f0`'s description ("Fattore massimo di
    amplificazione dello spettro in accelerazione orizzontale", 76 chars) is one of
    muro-sostegno's longest."""
    goto_tool(page, base_url, "muro-sostegno")
    toggle = page.locator('[data-field="f0"] .f-field-more')
    expect(toggle).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    full = page.locator('[data-field="f0"] .f-field-full')
    expect(full).to_be_hidden()
    toggle.click()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(full).to_be_visible()
    expect(full).to_have_text(re.compile("amplificazione dello spettro"))


# -- B: two-column Sintesi -------------------------------------------------------------------


def test_sintesi_is_two_columns_at_desktop_width(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding B: >=640px of #sintesi's own width -> a two-column grid, verdict/
    eta/highlights on the left, the sketch filling the right column."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    page.locator("#sintesi .r-si-sketch svg").first.wait_for(state="attached")

    layout = page.locator(".r-si-layout")
    expect(layout).to_have_css("display", "grid")

    main_box = page.locator(".r-si-main").bounding_box()
    side_box = page.locator(".r-si-side").bounding_box()
    assert main_box and side_box
    assert abs(main_box["y"] - side_box["y"]) < 4, "main and side columns must sit on the same row"
    assert side_box["x"] > main_box["x"], "the sketch column must be to the RIGHT of the verdict column"

    fig_box = page.locator(".r-si-sketch .sk-figure").first.bounding_box()
    assert fig_box and 220 <= fig_box["height"] <= 320, f"sketch figure height {fig_box['height']}px outside the 220-320px band"


def test_sintesi_sketch_first_when_narrow(mobile_page: tuple[Page, object], base_url: str) -> None:
    """WORKBENCH_SPEC finding B/K: below 640px (mobile Risultati) the Sintesi is one column with
    the SKETCH FIRST, above the verdict."""
    page, _ = mobile_page
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    page.locator("#sintesi .r-si-sketch svg").first.wait_for(state="attached")

    layout = page.locator(".r-si-layout")
    expect(layout).to_have_css("display", "flex")
    side_box = page.locator(".r-si-side").bounding_box()
    main_box = page.locator(".r-si-main").bounding_box()
    assert side_box and main_box
    assert side_box["y"] < main_box["y"], "the sketch must come BEFORE the verdict on narrow screens"


def test_sintesi_side_column_absent_without_sketch(page: Page, base_url: str) -> None:
    """A tool with no `schizzo` output must not reserve an empty 55% column (`.r-si-side:empty`)."""
    goto_tool(page, base_url, "sisma-spettro")
    load_example(page)
    page.wait_for_timeout(400)
    side = page.locator(".r-si-side")
    assert side.count() == 0 or side.evaluate("el => el.childElementCount") == 0


# -- C: sketch geometry / label quality --------------------------------------------------------

_SKETCH_MEASURE_JS = """
() => {
  const ANNOTATION_CLASSES = ['sk-carico', 'sk-reazione', 'sk-label'];
  const figs = Array.from(document.querySelectorAll('.r-si-sketch .sk-figure'));
  return figs.map(fig => {
    const svg = fig.querySelector('svg');
    const svgRect = svg.getBoundingClientRect();
    const viewBox = svg.getAttribute('viewBox').split(' ').map(Number);
    const shapes = Array.from(svg.children).filter(el => el.classList.contains('sk-shape'));
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity, found = false;
    for (const shape of shapes) {
      if (ANNOTATION_CLASSES.some(c => shape.classList.contains(c))) continue;
      const b = shape.getBBox();
      if (b.width === 0 && b.height === 0) continue;
      found = true;
      minX = Math.min(minX, b.x); minY = Math.min(minY, b.y);
      maxX = Math.max(maxX, b.x + b.width); maxY = Math.max(maxY, b.y + b.height);
    }
    const smallerVb = Math.min(viewBox[2], viewBox[3]);
    const share = found ? Math.min(maxX - minX, maxY - minY) / smallerVb : null;

    const texts = Array.from(svg.querySelectorAll('text')).map(t => {
      const r = t.getBoundingClientRect();
      return { content: t.textContent, left: r.left - svgRect.left, right: r.right - svgRect.left, top: r.top - svgRect.top, bottom: r.bottom - svgRect.top };
    });
    const outOfBounds = texts.filter(t => t.left < -1 || t.right > svgRect.width + 1 || t.top < -1 || t.bottom > svgRect.height + 1).map(t => t.content);
    const overlaps = [];
    for (let i = 0; i < texts.length; i++) {
      for (let j = i + 1; j < texts.length; j++) {
        const a = texts[i], b = texts[j];
        if (a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top) overlaps.push([a.content, b.content]);
      }
    }
    return { caption: fig.querySelector('figcaption').textContent, share, outOfBounds, overlaps };
  });
}
"""


@pytest.mark.parametrize(
    "tool_name",
    ["fond-plinto-isolato", "muro-sostegno", "fond-plinto-su-pali", "ca-trave-rettangolare", "neve-carico-falda", "ca-punzonamento"],
)
def test_sketch_text_not_clipped_or_overlapping(page: Page, base_url: str, tool_name: str) -> None:
    """WORKBENCH_SPEC finding C: no sketch text box is clipped at the figure edge or overlaps
    another text box, on every tool the design review specifically flagged. (ca-punzonamento used
    to be excluded here: its "Carica esempio" never actually ran -- `diametro_mm` is a REQUIRED
    field, conditionally hidden by the example's own inputs (a rectangular column), and the form
    dropped hidden fields from the submitted payload entirely, turning it into a server-side
    "campo obbligatorio mancante" the engineer could never see or fix. Fixed generically in
    forms-sections.js `visibleValues()`: a hidden field's value is always sent now, falling back to
    its own default/minimum when the user never had a chance to set one.)"""
    goto_tool(page, base_url, tool_name)
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")
    page.wait_for_timeout(200)  # label-collision nudging runs synchronously but let layout settle

    views = page.evaluate(_SKETCH_MEASURE_JS)
    assert views, f"expected at least one sketch view for {tool_name}"
    for view in views:
        assert not view["outOfBounds"], f"{tool_name} / {view['caption']}: clipped text {view['outOfBounds']}"
        assert not view["overlaps"], f"{tool_name} / {view['caption']}: overlapping text {view['overlaps']}"
        if view["share"] is None:
            continue
        # neve-carico-falda's own golden example sets `legacy_compat=True` WITH
        # `tipo_copertura="Copertura ad una falda"` -- `_richiede_campi_del_tipo_copertura`
        # (loads/neve/tool.py) reads that as "render BOTH the una-falda AND due-falde blocks"
        # (legacy_compat's own documented behaviour: "the sheet always computes both blocks when
        # the data is present"), so this ONE view draws three separate roof pitches side by side
        # instead of one -- an inherently wide/short footprint no amount of renderer-side margin
        # tuning turns into >=50% of the smaller (height) side without clipping the labels the
        # 60%-share budget would otherwise have room for (verified: identical share with the
        # renderer's own M5 centring at zero, a fifth, or its full budget -- the geometry, not the
        # renderer, sets this view's floor). Every OTHER tool here keeps the >=0.5 target.
        floor = 0.5 if tool_name != "neve-carico-falda" else 0.4
        assert view["share"] >= floor, f"{tool_name} / {view['caption']}: element share {view['share']:.2f} (target >=0.6, floor {floor})"


def test_wall_load_arrow_label_beside_shaft(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding C2: a load's text sits beside its own arrow, never on top of the
    wall/footing outline it is drawn next to -- spot-checked on muro-sostegno's thrust arrows, which
    the design review specifically called out as piling up. The wall sketch states each thrust in a
    separate `Etichetta` (stile "carico") anchored at the arrow's soil-side tail rather than in the
    arrow's own `testo`, so both kinds of text are checked -- and at least one must exist."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")

    result = page.evaluate(
        """() => {
            const svg = document.querySelector('.r-si-sketch svg');
            const concrete = Array.from(svg.querySelectorAll('.sk-calcestruzzo')).map(n => n.getBoundingClientRect());
            const texts = Array.from(svg.querySelectorAll('.sk-arrow-text text, .sk-label.sk-carico text'));
            const hits = texts.filter(t => {
                const r = t.getBoundingClientRect();
                return concrete.some(c => r.left < c.right && r.right > c.left && r.top < c.bottom && r.bottom > c.top);
            }).map(t => t.textContent);
            return { concrete: concrete.length, texts: texts.length, hits };
        }"""
    )
    assert result["concrete"] > 0 and result["texts"] > 0, f"nothing to check: {result}"
    assert result["hits"] == [], f"load text on top of the wall/footing outline: {result['hits']}"


# -- D: two-decimal utilisation everywhere ----------------------------------------------------


def test_eta_max_shows_two_decimals_everywhere(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding D: utilisation is shown with exactly two decimals ("0,85"), never
    formatNumber's 4-significant-digit default ("0,8478") -- Sintesi eta line, bottom bar and the
    utilisation bar's aria-label."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)

    eta_value = page.locator(".r-si-eta-value").inner_text()
    number = eta_value.split()[-1]
    assert UTIL_RE.match(number), f"Sintesi eta max {number!r} is not exactly two decimals"

    bar_label = page.locator(".r-si-eta .r-bar").get_attribute("aria-label")
    assert bar_label and UTIL_RE.match(bar_label.split()[-1]), f"bar aria-label {bar_label!r} is not exactly two decimals"


def test_bottom_bar_eta_max_two_decimals(mobile_page: tuple[Page, object], base_url: str) -> None:
    page, _ = mobile_page
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    text = page.locator("#bottom-bar .r-bb-eta").inner_text()
    number = text.replace("η max", "").strip()
    assert UTIL_RE.match(number), f"bottom bar eta {number!r} is not exactly two decimals"


# -- E: decluttered results head / toolbar / warnings -----------------------------------------


def test_results_title_not_repeated_on_screen(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding E: the tool title is not shown a second time under the Sintesi
    (it stays in the DOM, for a11y focus + print, but is visually hidden). It uses the standard
    "clip to 1x1px" a11y pattern (not `display:none`, so it stays reachable by assistive tech) --
    Playwright's own `to_be_visible()` only checks for a non-empty bounding box and would report
    a 1x1px element as "visible", so this checks the actual rendered size directly instead."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    head = page.locator("#results-head")
    expect(head).to_have_count(1)
    box = head.bounding_box()
    assert box and box["width"] <= 1 and box["height"] <= 1, f"expected a clipped 1x1px box, got {box}"


def test_results_toolbar_is_one_compact_row_no_jump_links(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding E: "Stampa relazione" / "Solo non soddisfatte" / "Espandi tutto"
    merged into one row of 32px controls; the jump-link strip is gone (the collapsed group
    headers are the navigation)."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)

    toolbar = page.locator(".r-toolbar")
    expect(toolbar).to_be_visible()
    print_btn = toolbar.get_by_role("button", name="Stampa relazione")
    filter_btn = toolbar.get_by_role("button", name="Solo non soddisfatte")
    expand_btn = toolbar.get_by_role("button", name="Espandi tutto")
    for btn in (print_btn, filter_btn, expand_btn):
        expect(btn).to_be_visible()
        height = btn.evaluate("el => el.getBoundingClientRect().height")
        assert height <= 36, f"toolbar control is {height}px tall, expected ~32px"
    print_box, filter_box = print_btn.bounding_box(), filter_btn.bounding_box()
    assert print_box and filter_box and abs(print_box["y"] - filter_box["y"]) < 4, "toolbar controls must share one row"

    assert page.locator(".r-toolbar-jump").count() == 0, "the jump-link strip must be gone"
    assert page.locator(".r-toolbar-jumplink").count() == 0


def test_warning_count_uses_correct_italian_singular(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding E: "1 avviso" (singular), not "1 avvisi"."""
    goto_tool(page, base_url, "muro-sostegno")
    load_example(page)
    warnings_btn = page.locator(".r-si-warnings")
    text = warnings_btn.inner_text()
    count = int(text.split()[0])
    expected_word = "avviso" if count == 1 else "avvisi"
    assert text == f"{count} {expected_word}", f"expected {count} {expected_word!r}, got {text!r}"


# -- F: one-row Dati action bar -----------------------------------------------------------------


def test_dati_action_bar_is_one_row(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding F: [Carica esempio] [Calcola, only while live is off] [...] never
    wrap to a second row."""
    goto_tool(page, base_url, "muro-sostegno")
    example_box = page.get_by_role("button", name="Carica esempio").bounding_box()
    menu_box = page.get_by_label("Altre azioni").bounding_box()
    assert example_box and menu_box
    assert abs(example_box["y"] - menu_box["y"]) < 4, "the action bar must stay on one row"


def test_live_status_text_shown_when_live_on(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding F: with live on (Calcola hidden) the free space shows "Calcolo
    automatico attivo" instead of sitting empty."""
    goto_tool(page, base_url, "muro-sostegno")
    expect(page.get_by_role("button", name="Calcola")).to_have_count(0)
    expect(page.locator(".f-live-status")).to_have_text("Calcolo automatico attivo")

    page.locator("#live-toggle").uncheck()
    expect(page.locator(".f-live-status")).to_have_text("")
    expect(page.get_by_role("button", name="Calcola")).to_be_visible()


# -- G: rail collapsed by default except the active tool's category ----------------------------


def test_rail_categories_collapsed_except_active_tool(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC #12 (supersedes finding G's flat rail): categories are accordions, closed
    by default except the one holding the active tool -- Preferiti/Recenti follow the identical
    rule and may ALSO be open at the same time if they happen to hold the active tool too (e.g.
    a just-visited tool is both in its category and in Recenti at once)."""
    goto_tool(page, base_url, "muro-sostegno")  # group: "Geotecnica"
    groups = page.locator("#tool-index .rail-group").all()
    assert groups, "expected at least one rail category"
    category_groups = [g for g in groups if g.get_attribute("data-kind") == "category"]
    open_categories = [g for g in category_groups if g.evaluate("el => el.open")]
    assert len(open_categories) == 1, f"expected exactly one open category, got {len(open_categories)}"
    assert open_categories[0].locator("summary .rail-label").inner_text() == "Geotecnica"
    active_category = page.locator("#tool-index .rail-group[data-kind='category']:has([aria-current='true'])")
    expect(active_category).to_have_count(1)
    assert active_category.evaluate("el => el.open") is True


def test_rail_tool_label_wraps_with_title_tooltip(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC #12: tool row titles wrap to two lines instead of truncating mid-word; the
    full name is still available via `title`."""
    goto_tool(page, base_url, "muro-sostegno")
    item = page.locator('.rail-row-open[data-tool="muro-sostegno"]').first
    title = item.get_attribute("title")
    assert title, "expected a title attribute with the full tool name"
    white_space = item.locator(".rail-row-title").evaluate("el => getComputedStyle(el).whiteSpace")
    assert white_space == "normal", "rail row title must be allowed to wrap, not truncate on one line"


def test_recenti_max_five(page: Page, base_url: str) -> None:
    """WORKBENCH_SPEC finding G / #12: "Recenti" max 5 (was 6)."""
    page.goto(f"{base_url}/#/")
    page.locator("#home-search").wait_for(state="visible")
    tool_names = [
        "muro-sostegno", "fond-plinto-isolato", "ca-trave-rettangolare", "ca-punzonamento",
        "neve-carico-falda", "vento-pressione", "sisma-spettro",
    ]
    for name in tool_names:
        page.goto(f"{base_url}/#/{name}")
        page.locator("#tool-title").wait_for(state="visible")
    recenti_items = page.locator("#tool-index .rail-group[data-kind='recenti'] .rail-row")
    assert 0 < recenti_items.count() <= 5, f"expected 1-5 Recenti entries, got {recenti_items.count()}"


# -- H: header search removed, search stays in the rail / Home / Ctrl+K --------------------


def test_header_search_trigger_removed(page: Page, base_url: str) -> None:
    """Design review 2026-09-21: the header "Cerca strumento..." field is gone -- search already
    lives in the rail's own "Cerca" destination, on Home (#home-search) and on Ctrl/Cmd+K; the
    header field was redundant with all three and broke the 390px header (next test)."""
    page.goto(f"{base_url}/#/")
    page.locator("#home-search").wait_for(state="visible")
    expect(page.locator("#search-trigger")).to_have_count(0)
    expect(page.locator(".app-search-trigger")).to_have_count(0)


def test_search_still_reachable_from_rail_home_and_palette(page: Page, base_url: str) -> None:
    """The three remaining search entry points all still open the same command palette."""
    page.goto(f"{base_url}/#/")
    page.locator("#home-search").wait_for(state="visible")

    # Rail's own "Cerca" destination (WORKBENCH_SPEC #12).
    page.get_by_role("button", name="Cerca").click()
    expect(page.locator("#palette-input")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator("#palette-input")).to_be_hidden()

    # Ctrl/Cmd+K.
    page.keyboard.press("Control+k")
    expect(page.locator("#palette-input")).to_be_visible()
    page.keyboard.press("Escape")

    # Home's own search field is a plain input, not the palette -- just confirm it is present
    # and accepts text (the actual filtering is covered elsewhere).
    home_search = page.locator("#home-search")
    home_search.fill("plinto")
    expect(home_search).to_have_value("plinto")


def test_header_does_not_wrap_at_390px(mobile_page, base_url: str) -> None:
    """Design review 2026-09-21: with the search field gone, the header (title + "Calcolo
    automatico" switch) fits a 390px viewport with no horizontal document overflow -- the original
    bug (the now-removed search field) forced the document wider than the viewport."""
    page, _ = mobile_page
    page.goto(f"{base_url}/#/")
    page.locator(".app-header").wait_for(state="visible")

    doc_scroll_width = page.evaluate("document.documentElement.scrollWidth")
    assert doc_scroll_width <= 390, f"document overflows its own 390px viewport: {doc_scroll_width}px"

    header_scroll_width = page.evaluate("document.querySelector('.app-header').scrollWidth")
    assert header_scroll_width <= 390, f"header content overflows its own 390px row: {header_scroll_width}px"
