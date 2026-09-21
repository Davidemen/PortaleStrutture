// One small function per Sketch shape kind (src/strutture/shared/sketch.py) -> SVG nodes.
// Element creation goes only through `svgNode` (document.createElementNS), never innerHTML.
// Colour/fill/line-weight live in CSS classes `sk-<stile>` (css/sketch.css); everything here is
// SVG presentation attributes only (CSP `default-src 'self'`: no style="").
import { toScreen, dimensionOffset, diagramPolygon } from "./sketch-fit.js";
import { symbolTspans, symbolAwareTspans, splitSymbolPrefix } from "./symbols.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const TEXT_PX = 11.5; // constant on-screen size regardless of model scale (spec: 11-12px, never <10)
const TICK_PX = 6; // dimension 45deg tick half-length, on screen
const GAP_PX = 4; // text gap above its anchor line, on screen
const BAR_MIN_PX = 5; // bars minimum on-screen diameter (review finding 17: 2px read as unreadable dust)
const ARROW_PX = 9; // arrowhead length, on screen

// Creates (or reuses+patches) one SVG element; unset attrs are removed. The one place
// document.createElementNS is called from this module.
export function svgNode(tag, attrs = {}, existing = null) {
  const node = existing && existing.tagName?.toLowerCase() === tag ? existing : document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null) node.removeAttribute(key);
    else node.setAttribute(key, String(value));
  }
  return node;
}

function pt(p) {
  const [x, y] = toScreen(p);
  return `${x.toFixed(4)},${y.toFixed(4)}`;
}

// Text that stays TEXT_PX css px tall regardless of the view's model-to-screen scale: drawn at
// local (0,0) inside a group translated to its anchor and scaled by 1/s, cancelling the ambient
// viewBox zoom. `dy` is a plain css-px offset (local space, post-cancel).
function textAt(anchor, s, { className, textAnchor = "middle", dx = 0, dy = 0 }, build) {
  const [x, y] = toScreen(anchor);
  const g = svgNode("g", { class: className, transform: `translate(${x.toFixed(4)} ${y.toFixed(4)}) scale(${(1 / s).toFixed(6)})` });
  const text = svgNode("text", { x: dx, y: dy, "text-anchor": textAnchor, "font-size": TEXT_PX });
  build(text);
  g.append(text);
  return g;
}

// `fill` is a presentation attribute (CSP-safe, no style=""), which CSS classes always outrank --
// so a `terreno` dotted-pattern fill must be set here rather than in the `.sk-terreno` rule.
function fillFor(shape, ctx) {
  return shape.stile === "terreno" ? `url(#sk-terreno-${ctx.idPrefix || ""}${ctx.viewIndex})` : undefined;
}

export function buildRect(shape, ctx) {
  const [x1, y1] = toScreen([shape.x, shape.y]);
  const [x2, y2] = toScreen([shape.x + shape.w, shape.y + shape.h]);
  return svgNode("rect", {
    class: `sk-shape sk-${shape.stile}`,
    x: Math.min(x1, x2), y: Math.min(y1, y2), width: Math.abs(x2 - x1), height: Math.abs(y2 - y1),
    fill: fillFor(shape, ctx), "vector-effect": "non-scaling-stroke",
  });
}

export function buildPolygon(shape, ctx) {
  return svgNode("polygon", {
    class: `sk-shape sk-${shape.stile}`,
    points: shape.punti.map(pt).join(" "),
    fill: fillFor(shape, ctx), "vector-effect": "non-scaling-stroke",
  });
}

// `tratteggio` (e.g. radius of relative stiffness, control perimeters): dashed outline, no
// fill, whatever the stile -- `sk-tratteggio` in css/sketch.css carries both overrides.
export function buildCircle(shape) {
  const [cx, cy] = toScreen(shape.centro);
  const cls = `sk-shape sk-${shape.stile}${shape.tratteggio ? " sk-tratteggio" : ""}`;
  return svgNode("circle", { class: cls, cx: cx.toFixed(4), cy: cy.toFixed(4), r: shape.r, "vector-effect": "non-scaling-stroke" });
}

export function buildLine(shape) {
  const [x1, y1] = toScreen(shape.p1);
  const [x2, y2] = toScreen(shape.p2);
  return svgNode("line", {
    class: `sk-shape sk-${shape.stile}${shape.tratteggio ? " sk-tratteggio" : ""}`,
    x1, y1, x2, y2, "vector-effect": "non-scaling-stroke",
  });
}

// Finding C2: "keep arrow texts beside their arrow (left of a leftward arrow, above a downward
// one)" -- the label sits on whichever side of the tip the shaft does NOT occupy, based on the
// arrow's own screen-space direction, instead of always anchoring "start, above" regardless of
// which way it points (which used to pile the text on top of the shaft for a leftward/upward arrow).
function arrowLabelPlacement(dxScreen, dyScreen) {
  if (Math.abs(dxScreen) >= Math.abs(dyScreen)) {
    // Horizontal-ish: text behind the tail, vertically centred on the shaft's own line.
    return { textAnchor: dxScreen > 0 ? "end" : "start", dx: dxScreen > 0 ? -GAP_PX : GAP_PX, dy: TEXT_PX * 0.35 };
  }
  // Vertical-ish: text above the tail of a downward arrow, below the tail of an upward one.
  return { textAnchor: "middle", dx: 0, dy: dyScreen > 0 ? -GAP_PX : GAP_PX + TEXT_PX * 0.8 };
}

export function buildArrow(shape, ctx) {
  const g = svgNode("g", { class: `sk-shape sk-${shape.stile}` });
  const [x1, y1] = toScreen(shape.coda);
  const [x2, y2] = toScreen(shape.punta);
  const prefix = ctx.idPrefix || "";
  const markerId = shape.stile === "reazione" ? `sk-arrow-reazione-${prefix}${ctx.viewIndex}` : `sk-arrow-carico-${prefix}${ctx.viewIndex}`;
  g.append(svgNode("line", { x1, y1, x2, y2, class: "sk-arrow-shaft", "vector-effect": "non-scaling-stroke", "marker-end": `url(#${markerId})` }));
  if (shape.testo) {
    // At the TAIL (`coda`), the free end: at the tip the text sat across the shaft and on top of
    // whatever the arrow points at. Same model as the Python overlap lint (test_sketch_layout.py),
    // which every sketch author composes against.
    const { textAnchor, dx, dy } = arrowLabelPlacement(x2 - x1, y2 - y1);
    g.append(textAt(shape.coda, ctx.s, { className: "sk-arrow-text", textAnchor, dx, dy }, (t) => { t.append(...symbolAwareTspans(shape.testo)); }));
  }
  return g;
}

function tick(atScreen, dirScreen, len) {
  const dlen = Math.hypot(dirScreen[0], dirScreen[1]) || 1;
  const ux = dirScreen[0] / dlen, uy = dirScreen[1] / dlen;
  const c = Math.SQRT1_2;
  const rx = ux * c - uy * c, ry = ux * c + uy * c; // rotate direction by 45deg
  return svgNode("line", {
    x1: atScreen[0] - rx * len, y1: atScreen[1] - ry * len, x2: atScreen[0] + rx * len, y2: atScreen[1] + ry * len,
    class: "sk-quota-tick", "vector-effect": "non-scaling-stroke",
  });
}

// Dimension (Quota) has no `stile` in the data contract: always rendered as "quota". Extension
// lines to p1/p2, the offset line with 45deg ticks at its ends, text upright and centred above.
export function buildDimension(shape, ctx) {
  const g = svgNode("g", { class: "sk-shape sk-quota" });
  const { o1, o2 } = dimensionOffset(shape);
  const [p1x, p1y] = toScreen(shape.p1);
  const [p2x, p2y] = toScreen(shape.p2);
  const [o1x, o1y] = toScreen(o1);
  const [o2x, o2y] = toScreen(o2);
  g.append(svgNode("line", { x1: p1x, y1: p1y, x2: o1x, y2: o1y, class: "sk-quota-ext", "vector-effect": "non-scaling-stroke" }));
  g.append(svgNode("line", { x1: p2x, y1: p2y, x2: o2x, y2: o2y, class: "sk-quota-ext", "vector-effect": "non-scaling-stroke" }));
  g.append(svgNode("line", { x1: o1x, y1: o1y, x2: o2x, y2: o2y, class: "sk-quota-line", "vector-effect": "non-scaling-stroke" }));
  const tickLen = TICK_PX / ctx.s;
  g.append(tick([o1x, o1y], [o2x - o1x, o2y - o1y], tickLen));
  g.append(tick([o2x, o2y], [o2x - o1x, o2y - o1y], tickLen));
  const midScreen = [(o1x + o2x) / 2, (o1y + o2y) / 2];
  const textGroup = svgNode("g", { class: "sk-quota-text", transform: `translate(${midScreen[0].toFixed(4)} ${midScreen[1].toFixed(4)}) scale(${(1 / ctx.s).toFixed(6)})` });
  // Review finding 9: a near-VERTICAL quota line (screen |dy|>|dx| -- a height/depth dimension
  // running top to bottom beside an element, PLI/TCO/NAC/MUR) used to always centre its text ON
  // the line, same as the horizontal case -- for a vertical line that runs the text straight
  // through whatever solid geometry sits next to it. Anchored to the OUTER side instead (away
  // from the element, continuing past the offset line the same direction `dimensionOffset` already
  // pushed it) and centred vertically on the line's own midpoint height; the horizontal case is
  // unchanged (centred above the line, as before).
  const dxScreen = o2x - o1x, dyScreen = o2y - o1y;
  const vertical = Math.abs(dyScreen) > Math.abs(dxScreen);
  const outward = vertical ? Math.sign(o1x - p1x) || 1 : 0;
  const textAttrs = vertical
    ? { x: outward * GAP_PX, y: 0, "text-anchor": outward < 0 ? "end" : "start", "dominant-baseline": "middle" }
    : { x: 0, y: -GAP_PX, "text-anchor": "middle" };
  const text = svgNode("text", { ...textAttrs, "font-size": TEXT_PX });
  text.append(...symbolAwareTspans(shape.testo));
  textGroup.append(text);
  g.append(textGroup);
  return g;
}

// When `testo` redundantly repeats `simbolo` ("q_s2 = 6,16 kN/m²" alongside simbolo="q_s2" --
// sketch.py's own COMPOSITION RULES say testo should be the value ONLY, but this stays defensive
// against data that doesn't) print the symbol once, not twice: strip the leading "simbolo = "
// before appending, falling back to `testo` verbatim when it is already value-only as intended.
function labelValueText(testo, simbolo) {
  if (!testo) return null;
  const split = splitSymbolPrefix(testo);
  return split && split.symbol === simbolo ? split.rest : testo;
}

export function buildLabel(shape, ctx) {
  return textAt(shape.punto, ctx.s, { className: `sk-shape sk-${shape.stile} sk-label`, textAnchor: shape.ancora }, (t) => {
    if (shape.simbolo) {
      t.append(...symbolTspans(shape.simbolo));
      const value = labelValueText(shape.testo, shape.simbolo);
      // "M = 1 kNm", like a dimension's or an arrow's own text -- every symbol label in the
      // sketches states a quantity and its value, and a bare "M 1 kNm" reads as a typo.
      if (value) t.append(document.createTextNode(` = ${value}`));
    } else {
      t.append(...symbolAwareTspans(shape.testo));
    }
  });
}

export function buildBars(shape, ctx) {
  const g = svgNode("g", { class: `sk-shape sk-${shape.stile}` });
  const rUser = Math.max(shape.diametro / 2, BAR_MIN_PX / 2 / ctx.s);
  for (const centro of shape.centri) {
    const [cx, cy] = toScreen(centro);
    g.append(svgNode("circle", { cx, cy, r: rUser, "vector-effect": "non-scaling-stroke" }));
  }
  return g;
}

// Ordinate hatching: thin lines from the baseline to the envelope, the drawing-office convention
// for a distributed pressure -- without it a near-uniform base pressure under a footing reads as
// one more block of concrete. One line every ~HATCH_STEP_PX on screen, ends included.
const HATCH_STEP_PX = 10;
const HATCH_MIN = 3;
const HATCH_MAX = 40;

function lerpPoint(a, b, t) {
  return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
}

function ordinateAt(ordinates, t) {
  if (ordinates.length === 1) return ordinates[0];
  const pos = t * (ordinates.length - 1);
  const i = Math.min(Math.floor(pos), ordinates.length - 2);
  return lerpPoint(ordinates[i], ordinates[i + 1], pos - i);
}

function buildHatch(shape, ordinates, s) {
  const [b1, b2] = shape.base;
  const lengthPx = Math.hypot(b2[0] - b1[0], b2[1] - b1[1]) * s;
  const count = Math.max(HATCH_MIN, Math.min(HATCH_MAX, Math.round(lengthPx / HATCH_STEP_PX)));
  return Array.from({ length: count + 1 }, (_, k) => {
    const t = k / count;
    const [x1, y1] = toScreen(lerpPoint(b1, b2, t));
    const [x2, y2] = toScreen(ordinateAt(ordinates, t));
    return svgNode("line", { x1, y1, x2, y2, class: "sk-diagram-hatch", "vector-effect": "non-scaling-stroke" });
  });
}

// A label sits OUTSIDE the envelope, past its ordinate tip: below the tip when the diagram hangs
// under its base (a base pressure), above it otherwise. It used to be always above the tip -- for a
// hanging diagram that is INSIDE the polygon, on top of the footing edge and whatever is drawn there.
function hangsBelowBase(shape, ordinates) {
  const n = shape.valori.length;
  const iMax = shape.valori.reduce((best, v, i) => (Math.abs(v) > Math.abs(shape.valori[best]) ? i : best), 0);
  const onBase = lerpPoint(shape.base[0], shape.base[1], n === 1 ? 0 : iMax / (n - 1));
  const dx = ordinates[iMax][0] - onBase[0], dy = ordinates[iMax][1] - onBase[1];
  return dy < 0 && Math.abs(dy) >= Math.abs(dx); // model space, y up
}

export function buildDiagram(shape, ctx) {
  const g = svgNode("g", { class: `sk-shape sk-${shape.stile}` });
  const poly = diagramPolygon(shape, ctx.side);
  const ordinates = poly.slice(1, -1);
  g.append(svgNode("polygon", { points: poly.map(pt).join(" "), class: "sk-diagram-fill", "vector-effect": "non-scaling-stroke" }));
  if (ordinates.length > 0) g.append(...buildHatch(shape, ordinates, ctx.s));
  const [bx1, by1] = toScreen(shape.base[0]);
  const [bx2, by2] = toScreen(shape.base[1]);
  g.append(svgNode("line", { x1: bx1, y1: by1, x2: bx2, y2: by2, class: "sk-diagram-base", "vector-effect": "non-scaling-stroke" }));
  const dy = ordinates.length > 0 && hangsBelowBase(shape, ordinates) ? TEXT_PX + GAP_PX : -GAP_PX;
  (shape.etichette ?? []).forEach((label, i) => {
    if (!label || !poly[i + 1]) return;
    g.append(textAt(poly[i + 1], ctx.s, { className: "sk-diagram-text", textAnchor: "middle", dy }, (t) => { t.append(...symbolAwareTspans(label)); }));
  });
  return g;
}

function arrowMarker(id, className, s) {
  const w = ARROW_PX / s, h = (ARROW_PX * 0.8) / s;
  const marker = svgNode("marker", { id, markerUnits: "userSpaceOnUse", markerWidth: w, markerHeight: h, refX: 10, refY: 4, orient: "auto-start-reverse", viewBox: "0 0 10 8" });
  marker.append(svgNode("path", { d: "M0,0 L10,4 L0,8 Z", class: className }));
  return marker;
}

// Per-view arrowhead markers (unique ids per view so several figures can share one document).
// `idPrefix` (review finding 7): the printed report builds a SECOND, independent copy of the same
// sketch into its own print-only container while the interactive one stays in the DOM (merely
// hidden, not removed, by print.css) -- without a distinct prefix both copies mint the identical
// `sk-arrow-carico-0`/`sk-terreno-0` ids for the same view index, and every `url(#id)` fill/
// marker-end reference in the DOCUMENT resolves to whichever element got that id FIRST, which is
// not reliably the printed one. `relazione.js` passes `{idPrefix:"p"}`; the interactive Sintesi
// renders with none (its own single copy is rebuilt in place, never duplicated).
export function buildArrowMarkers(viewIndex, s, idPrefix = "") {
  return [
    arrowMarker(`sk-arrow-carico-${idPrefix}${viewIndex}`, "sk-arrowhead-carico", s),
    arrowMarker(`sk-arrow-reazione-${idPrefix}${viewIndex}`, "sk-arrowhead-reazione", s),
  ];
}

// `terreno` dotted-pattern fill, tile sized so the dots read as a constant ~6px pitch on
// screen regardless of the view's model-to-screen scale.
export function buildTerrenoPattern(viewIndex, s, idPrefix = "") {
  const pitch = 6 / s;
  const pattern = svgNode("pattern", { id: `sk-terreno-${idPrefix}${viewIndex}`, patternUnits: "userSpaceOnUse", width: pitch, height: pitch });
  pattern.append(svgNode("circle", { cx: pitch / 2, cy: pitch / 2, r: Math.max(pitch * 0.12, 0.35 / s), class: "sk-terreno-dot" }));
  return pattern;
}

const BUILDERS = {
  rect: buildRect, polygon: buildPolygon, circle: buildCircle, line: buildLine, arrow: buildArrow,
  dimension: buildDimension, label: buildLabel, bars: buildBars, diagram: buildDiagram,
};

export function buildShape(shape, ctx) {
  const builder = shape && BUILDERS[shape.kind];
  return builder ? builder(shape, ctx) : null;
}
