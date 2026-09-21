"""WORKBENCH_SPEC §5 sketch renderer quality -- design-lead review ("a bit messy and cramped" on
neve-accumulo) + the user's own findings M1-M6: every `stile` visible for every shape kind,
dimension lines never landing on the line they measure, symbol subscripts (never a raw "_") in
dimension/arrow/diagram text, and the drawing centred in its figure."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page

from ._actions import goto_tool, load_example

pytestmark = pytest.mark.e2e

SKETCH_TOOLS = ["fond-plinto-isolato", "muro-sostegno", "fond-plinto-su-pali", "ca-trave-rettangolare", "neve-carico-falda", "neve-accumulo", "ca-punzonamento"]

_SKETCH_TEXT_JS = "() => Array.from(document.querySelectorAll('.r-si-sketch svg text')).map(t => t.textContent)"

_DIMENSION_OFFSET_JS = """
() => {
  const results = [];
  document.querySelectorAll('.r-si-sketch svg .sk-quota').forEach((g) => {
    const svg = g.closest('svg');
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    g.querySelectorAll('.sk-quota-ext').forEach((line) => {
      const p1 = new DOMPoint(Number(line.getAttribute('x1')), Number(line.getAttribute('y1'))).matrixTransform(ctm);
      const p2 = new DOMPoint(Number(line.getAttribute('x2')), Number(line.getAttribute('y2'))).matrixTransform(ctm);
      results.push(Math.hypot(p2.x - p1.x, p2.y - p1.y));
    });
  });
  return results;
}
"""

_CENTER_JS = """
() => {
  const ANNOTATION_CLASSES = ['sk-carico', 'sk-reazione', 'sk-label'];
  // Review finding 9: a quota's TEXT sub-group can now extend to one side of its line
  // independently (anchored to the outer side for a vertical dimension, instead of centred on
  // it) -- the same kind of annotation reach `sk-label`'s own text already is, and excluded from
  // this measurement for the same reason: it is not the ELEMENT's own structural geometry. Only a
  // quota's line/tick geometry (still very much structural: it traces the element's own extent)
  // counts toward the box.
  // Same for a diagram's end labels: they now sit OUTSIDE the envelope, past the ordinate tips
  // (sketch-shapes.js buildDiagram), so the group's own getBBox() would count that text as part of
  // the element -- only the envelope, its hatching and its baseline are structural.
  const bboxOf = (shape) => {
    const isQuota = shape.classList.contains('sk-quota');
    const isDiagram = shape.querySelector(':scope > .sk-diagram-fill') !== null;
    if (!isQuota && !isDiagram) return shape.getBBox();
    const selector = isQuota ? '.sk-quota-ext, .sk-quota-line, .sk-quota-tick' : '.sk-diagram-fill, .sk-diagram-base';
    const lineNodes = Array.from(shape.querySelectorAll(selector));
    if (lineNodes.length === 0) return { x: 0, y: 0, width: 0, height: 0 };
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const node of lineNodes) {
      const nb = node.getBBox();
      x0 = Math.min(x0, nb.x); y0 = Math.min(y0, nb.y);
      x1 = Math.max(x1, nb.x + nb.width); y1 = Math.max(y1, nb.y + nb.height);
    }
    return { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
  };
  return Array.from(document.querySelectorAll('.r-si-sketch .sk-figure')).map((fig) => {
    const svg = fig.querySelector('svg');
    const vb = svg.viewBox.baseVal;
    const shapes = Array.from(svg.children).filter((el) => el.classList.contains('sk-shape'));
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity, found = false;
    for (const shape of shapes) {
      if (ANNOTATION_CLASSES.some((c) => shape.classList.contains(c))) continue;
      const b = bboxOf(shape);
      if (b.width === 0 && b.height === 0) continue;
      found = true;
      minX = Math.min(minX, b.x); minY = Math.min(minY, b.y);
      maxX = Math.max(maxX, b.x + b.width); maxY = Math.max(maxY, b.y + b.height);
    }
    if (!found) return null;
    const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    const vbcx = vb.x + vb.width / 2, vbcy = vb.y + vb.height / 2;
    return {
      caption: fig.querySelector('figcaption').textContent,
      offX: vb.width > 0 ? Math.abs(cx - vbcx) / vb.width : 0,
      offY: vb.height > 0 ? Math.abs(cy - vbcy) / vb.height : 0,
    };
  }).filter(Boolean);
}
"""


@pytest.mark.parametrize("tool_name", SKETCH_TOOLS)
def test_no_raw_underscore_in_sketch_text(page: Page, base_url: str, tool_name: str) -> None:
    """M3: dimension/arrow/diagram texts carrying their own "simbolo = valore" go through the
    same subscript tokenizer as a label's `simbolo` field -- the raw "_" must never reach the DOM
    (ca-punzonamento included: the UI-path bug that used to keep its sketch from ever rendering is
    fixed generically in forms-sections.js, not with a tool-specific workaround)."""
    goto_tool(page, base_url, tool_name)
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")
    page.wait_for_timeout(200)
    texts = page.evaluate(_SKETCH_TEXT_JS)
    assert texts, f"{tool_name}: expected at least one sketch text"
    offending = [t for t in texts if "_" in t]
    assert not offending, f"{tool_name}: raw underscore in sketch text {offending!r}"


@pytest.mark.parametrize("tool_name", SKETCH_TOOLS)
def test_dimension_lines_clear_their_own_segment(page: Page, base_url: str, tool_name: str) -> None:
    """M2: every dimension line sits >=20px (a 2px margin under the 22px minimum) from the
    segment it measures -- the extension line's own on-screen length IS that offset."""
    goto_tool(page, base_url, tool_name)
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")
    page.wait_for_timeout(200)
    offsets = page.evaluate(_DIMENSION_OFFSET_JS)
    if not offsets:
        pytest.skip(f"{tool_name}: no dimension lines in this example")
    for offset in offsets:
        assert offset >= 20, f"{tool_name}: a dimension line sits only {offset:.1f}px from its segment"


@pytest.mark.parametrize("tool_name", SKETCH_TOOLS)
def test_drawing_centred_in_its_figure(page: Page, base_url: str, tool_name: str) -> None:
    """M5: the fitted drawing's own (structural) bounding box is centred in its figure, within
    10% of the figure's centre on each axis -- an annotation reaching further on one side must
    never visually skew the element itself off-centre."""
    goto_tool(page, base_url, tool_name)
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")
    page.wait_for_timeout(200)
    views = page.evaluate(_CENTER_JS)
    assert views, f"{tool_name}: expected at least one sketch view"
    for view in views:
        assert view["offX"] <= 0.10 + 1e-6, f"{tool_name} / {view['caption']}: x-offset {view['offX']:.3f} exceeds 10%"
        assert view["offY"] <= 0.10 + 1e-6, f"{tool_name} / {view['caption']}: y-offset {view['offY']:.3f} exceeds 10%"


def test_pressione_polygon_has_visible_fill_and_stroke(page: Page, base_url: str) -> None:
    """M1: neve-accumulo's snow-drift triangle is a `Poligono` with `stile="pressione"` -- it used
    to inherit `fill:none` with no stroke of its own and never show up at all."""
    goto_tool(page, base_url, "neve-accumulo")
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")

    style = page.evaluate(
        """() => {
            const poly = document.querySelector('.r-si-sketch polygon.sk-pressione');
            if (!poly) return null;
            const cs = getComputedStyle(poly);
            return { fillOpacity: Number(cs.fillOpacity), stroke: cs.stroke, strokeWidth: parseFloat(cs.strokeWidth) };
        }"""
    )
    assert style, "expected a <polygon class=\"sk-pressione\"> for the snow-drift load profile"
    assert style["fillOpacity"] > 0, f"pressione polygon has no visible fill: {style!r}"
    assert style["stroke"] not in (None, "none", ""), f"pressione polygon has no stroke: {style!r}"
    assert style["strokeWidth"] > 0, f"pressione polygon stroke-width is 0: {style!r}"


def test_sketch_nota_shown_as_caption_and_in_aria_label(page: Page, base_url: str) -> None:
    """M6: `Sketch.nota` ("Schema non in scala") is a small caption under the views AND already
    folded into each view's own `aria-label` (sketch.js `ariaLabel`)."""
    goto_tool(page, base_url, "neve-accumulo")
    load_example(page)
    page.locator(".r-si-sketch svg").first.wait_for(state="attached")

    caption = page.locator(".r-si-sketch .sk-nota")
    assert caption.count() == 1
    assert "non in scala" in caption.inner_text().lower()
    aria_label = page.locator(".r-si-sketch svg").first.get_attribute("aria-label") or ""
    assert "non in scala" in aria_label.lower(), f"aria-label must include the nota, got: {aria_label!r}"
