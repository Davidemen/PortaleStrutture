// Pure geometry for the sketch renderer (WORKBENCH_SPEC.md #5, findings C1/C3): bounding box of a
// Vista incl. dimension offsets and diagram ordinates; uniform scale; y flip; padding.
// No DOM, no globals -- unit-testable with `node --test`. Model space: metres, y UP
// (src/strutture/shared/sketch.py). Screen/SVG space: y DOWN.
import { TEXT_PX, LABEL_GAP_PX, longestTextPx } from "./sketch-text.js";

export const PADDING = 0.08;
const MIN_EXTENT = 1e-6;

// Finding C1: "the fitted bounding box must be driven by the GEOMETRY (solid shapes, lines,
// diagrams, dimension lines)" -- these kinds always drive the box outright. `arrow`/`label` are
// NOT in this set: a load arrow's tip is often placed at an arbitrary "visually long enough"
// distance rather than a real structural coordinate, and a label anchor can sit well clear of the
// element it names -- letting either drive the box the same way a wall or footing outline does is
// exactly what shrank the actual element to ~20% of the figure (design review, finding C).
const STRUCTURAL_KINDS = new Set(["rect", "polygon", "circle", "line", "diagram", "dimension", "bars"]);
const ANNOTATION_KINDS = new Set(["arrow", "label"]);
// Finding C1: "the element should span >=60% of the figure's smaller side" -- annotation points
// outside the structural box may still nudge it open, but never by more than this fraction of the
// structural box's own smaller side, which keeps that share guaranteed regardless of how far an
// arrow/label happens to be placed.
const MIN_ELEMENT_SHARE = 0.6;
// M5: the slice of finding C1's OWN per-side annotation budget that re-centring (below) may
// additionally spend -- see the comment at its call site in `fitVista`.
const CENTER_BUDGET_SHARE = 0.05;

export function isFiniteNumber(n) {
  return typeof n === "number" && Number.isFinite(n);
}

function isFinitePoint(p) {
  return Array.isArray(p) && p.length === 2 && isFiniteNumber(p[0]) && isFiniteNumber(p[1]);
}

// The one place the model (y up) -> screen (y down) flip happens.
export function toScreen(point) {
  return [point[0], -point[1]];
}

// `distanza` metres, + = left of p1->p2 (model space, y up -> left is +90deg CCW of travel).
export function dimensionOffset(shape) {
  const [x1, y1] = shape.p1;
  const [x2, y2] = shape.p2;
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.hypot(dx, dy);
  if (!(len > MIN_EXTENT)) return { o1: shape.p1, o2: shape.p2 };
  const nx = -dy / len, ny = dx / len;
  const d = shape.distanza;
  return { o1: [x1 + nx * d, y1 + ny * d], o2: [x2 + nx * d, y2 + ny * d] };
}

// Diagram polygon vertices (model space): base start, one point per ordinate, base end --
// closing this path draws the pressure/moment envelope against the baseline. `side` is the
// view's reference (smaller-side) length; amplitude = shape.altezza_relativa * side, largest
// |valore| reaching it (sketch.py: "the renderer scales the largest |valore| to altezza_relativa
// of the view's smaller side").
export function diagramPolygon(shape, side) {
  const [x1, y1] = shape.base[0];
  const [x2, y2] = shape.base[1];
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.hypot(dx, dy);
  if (!(len > MIN_EXTENT) || !(side > 0)) return [shape.base[0], shape.base[1]];
  const nx = -dy / len, ny = dx / len;
  const n = shape.valori.length;
  const maxAbs = Math.max(...shape.valori.map((v) => Math.abs(v)), MIN_EXTENT);
  const amplitude = shape.altezza_relativa * side;
  const ordinates = shape.valori.map((v, i) => {
    const t = n === 1 ? 0 : i / (n - 1);
    const off = (v / maxAbs) * amplitude;
    return [x1 + dx * t + nx * off, y1 + dy * t + ny * off];
  });
  return [shape.base[0], ...ordinates, shape.base[1]];
}

// Model-space points a shape contributes to the bounding box. `side` sizes diagram ordinates --
// undefined on the preliminary pass (see fitVista), base points only then.
export function boundsPoints(shape, side) {
  switch (shape.kind) {
    case "rect":
      return [[shape.x, shape.y], [shape.x + shape.w, shape.y + shape.h]];
    case "polygon":
      return shape.punti;
    case "circle":
      return [[shape.centro[0] - shape.r, shape.centro[1] - shape.r], [shape.centro[0] + shape.r, shape.centro[1] + shape.r]];
    case "line":
      return [shape.p1, shape.p2];
    case "arrow":
      return [shape.coda, shape.punta];
    case "dimension": {
      const { o1, o2 } = dimensionOffset(shape);
      return [shape.p1, shape.p2, o1, o2];
    }
    case "label":
      return [shape.punto];
    case "bars": {
      const r = shape.diametro / 2;
      return shape.centri.flatMap(([x, y]) => [[x - r, y - r], [x + r, y + r]]);
    }
    case "diagram":
      return side === undefined ? [shape.base[0], shape.base[1]] : diagramPolygon(shape, side);
    default:
      return [];
  }
}

function extend(bounds, points) {
  let b = bounds;
  for (const p of points) {
    if (!isFinitePoint(p)) continue;
    const [x, y] = p;
    b = b
      ? { minX: Math.min(b.minX, x), maxX: Math.max(b.maxX, x), minY: Math.min(b.minY, y), maxY: Math.max(b.maxY, y) }
      : { minX: x, maxX: x, minY: y, maxY: y };
  }
  return b;
}

function boundsOfShapes(forme, side) {
  let b = null;
  for (const shape of forme) b = extend(b, boundsPoints(shape, side));
  return b;
}

function sizeOf(b) {
  return b ? { w: b.maxX - b.minX, h: b.maxY - b.minY } : { w: 0, h: 0 };
}

function referenceSide(size) {
  if (size.w > MIN_EXTENT && size.h > MIN_EXTENT) return Math.min(size.w, size.h);
  return Math.max(size.w, size.h, MIN_EXTENT);
}

function round6(n) {
  return Number(n.toFixed(6));
}

// A point outside [lo, hi] is pulled back to at most `maxExtra` past the edge it crossed --
// finding C1's fixed cap on how far an annotation point may push the box open.
function clampNear(value, lo, hi, maxExtra) {
  if (value < lo) return Math.max(value, lo - maxExtra);
  if (value > hi) return Math.min(value, hi + maxExtra);
  return value;
}

// M5 composition: an annotation reaching further on one side than the other (a label only to the
// RIGHT of the element, say) must never visually skew the DRAWING itself off-centre -- grows
// whichever side of `outer` needs LESS space toward the side that needs more, up to `maxExtra`
// (finding C1's own per-side annotation-clamp budget) past its own original requirement, so
// `inner`'s centre moves toward the centre of the box WITHOUT ever shrinking a side below what it
// already needed (that would clip real content -- e.g. a label already legitimately placed there)
// and without spending more than one more `maxExtra` share of margin on top of what finding C1
// already budgeted. A residual, partial off-centre is the trade when the gap is bigger than that.
function centerAround(inner, outer, maxExtra = Infinity) {
  const cx = (inner.minX + inner.maxX) / 2;
  const cy = (inner.minY + inner.maxY) / 2;
  const grow = (need, otherNeed) => (need < otherNeed ? Math.min(otherNeed, need + maxExtra) : need);
  const leftNeed = cx - outer.minX;
  const rightNeed = outer.maxX - cx;
  const topNeed = cy - outer.minY;
  const bottomNeed = outer.maxY - cy;
  const left = grow(leftNeed, rightNeed);
  const right = grow(rightNeed, leftNeed);
  const top = grow(topNeed, bottomNeed);
  const bottom = grow(bottomNeed, topNeed);
  return { minX: cx - left, maxX: cx + right, minY: cy - top, maxY: cy + bottom };
}

// -- Screen-space margins at the REAL box size ---------------------------------------------------
// The text margin is a fixed number of SCREEN px, but the viewBox is in model units -- and the
// px-per-unit scale itself depends on the margin (a wider margin means a wider viewBox means a
// smaller scale). Solving `scale * (content + 2*marginPx/scale) = boxPx` per axis gives the closed
// form below; the smaller of the two axes governs ("contain" fit, like the viewBox itself). An
// earlier version assumed a 320px box with no margin feedback: fine for a full-width figure, but a
// half-width one (two views side by side, ~170px) got half the margin it needed and clipped text.
const FALLBACK_BOX_WIDTH_PX = 320;
const MIN_CONTENT_SHARE = 0.35; // text margins never squeeze the drawing below this share of an axis

function normaliseBox(boxPx) {
  const width = boxPx && boxPx.width > 0 ? boxPx.width : FALLBACK_BOX_WIDTH_PX;
  const height = boxPx && boxPx.height > 0 ? boxPx.height : Infinity;
  return { width, height };
}

function axisScale(contentModel, marginsPx, boxAxisPx) {
  if (!Number.isFinite(boxAxisPx)) return Infinity;
  const contentPx = Math.max(boxAxisPx - marginsPx, boxAxisPx * MIN_CONTENT_SHARE);
  return contentPx / Math.max(contentModel, MIN_EXTENT);
}

// `margins` = {left, right, top, bottom} in screen px.
function marginAwareScale(contentModel, margins, box) {
  const scale = Math.min(
    axisScale(contentModel.w, margins.left + margins.right, box.width),
    axisScale(contentModel.h, margins.top + margins.bottom, box.height),
  );
  return Math.max(scale, MIN_EXTENT);
}

// Measured margins (sketch-measure.js) are as asymmetric as the text really is -- but M5 wants the
// ELEMENT near the middle of its figure, so the lighter side is topped up until the two differ by
// at most this share of the box (element at most half of it off-centre; M5's own target is 10%).
const MAX_MARGIN_IMBALANCE_SHARE = 0.16;

function balancedPair(a, b, boxAxisPx) {
  if (!Number.isFinite(boxAxisPx)) return [Math.max(a, b), Math.max(a, b)];
  const slack = boxAxisPx * MAX_MARGIN_IMBALANCE_SHARE;
  return [Math.max(a, b - slack), Math.max(b, a - slack)];
}

function balancedMargins(marginsPx, box) {
  const clean = (v) => (Number.isFinite(v) && v > 0 ? v : 0);
  const [left, right] = balancedPair(clean(marginsPx.left), clean(marginsPx.right), box.width);
  const [top, bottom] = balancedPair(clean(marginsPx.top), clean(marginsPx.bottom), box.height);
  return { left, right, top, bottom };
}

// Fits a Vista's shapes into a screen-space (y-down) viewBox. Two passes, per finding C1:
//  1. STRUCTURAL geometry (solid shapes, lines, diagrams, dimension lines) sets the box outright.
//  2. ANNOTATION points (arrow tips, label anchors) may extend it, but each is clamped to at most
//     `structuralSide * (1/MIN_ELEMENT_SHARE - 1)` past the structural edge -- guaranteeing the
//     structural element keeps >=60% of the final smaller side regardless of how far an arrow or
//     label happens to sit.
// A fixed SCREEN-SPACE margin (finding C3, converted to model units via an assumed render width)
// is then added for label/dimension/arrow TEXT, instead of letting the text itself drive the
// model-space box without bound. Returns null for degenerate input (no shapes, non-finite coords,
// zero-size box) -- the renderer then draws nothing for that view instead of throwing.
export function fitVista(vista, { padding = PADDING, boxPx = null, marginsPx = null } = {}) {
  if (!vista || !Array.isArray(vista.forme) || vista.forme.length === 0) return null;

  // Preliminary pass across EVERY shape (diagram amplitude needs a reference side before its own
  // ordinate points exist) -- unchanged two-pass shape from the original implementation, and the
  // `side` it produces is reused verbatim by the renderer at draw time (sketch.js), so the
  // diagram polygon fitted here and the one actually drawn always agree.
  const prelim = boundsOfShapes(vista.forme, undefined);
  if (!prelim) return null;
  const prelimSize = sizeOf(prelim);
  // Review finding 10: a diagram's amplitude (sketch-shapes.js diagramPolygon) scales off this
  // reference side -- for a very elongated view (its smaller side tiny next to the larger one,
  // e.g. a long, mostly-horizontal pressure/moment profile) that scaled the amplitude down to a
  // near-flat, illegible line. Floored at 30% of the larger side; a view closer to square is
  // unaffected (its own min(w,h) already clears that floor).
  const side = Math.max(referenceSide(prelimSize), Math.max(prelimSize.w, prelimSize.h) * 0.3);

  // M2: enforce the minimum dimension offset (+ stacking) using an APPROXIMATE scale derived from
  // this preliminary, unadjusted box -- good enough (same reasoning as the label margin below):
  // the fix only ever grows an offset that was too small to have meaningfully driven `prelim` in
  // the first place. `renderVista` (sketch.js) re-applies the same pure transform at the REAL
  // scale once it is known, so the drawn geometry always matches (or exceeds) what is fitted here.
  const box = normaliseBox(boxPx);
  const approxScalePrelim = box.width / Math.max(prelimSize.w, prelimSize.h, MIN_EXTENT);
  const forme = applyDimensionOffsets(vista.forme, approxScalePrelim, side);

  const structural = forme.filter((s) => s && STRUCTURAL_KINDS.has(s.kind));
  const annotations = forme.filter((s) => s && ANNOTATION_KINDS.has(s.kind));

  // A view made only of arrows/labels (rare, e.g. a legend) has no structural geometry to anchor
  // on -- fall back to every shape so something still renders.
  let modelBounds = boundsOfShapes(structural, side) || boundsOfShapes(forme, side);
  if (!modelBounds) return null;
  const structuralBounds = modelBounds; // captured before annotations below can skew it off-centre
  const structuralSide = referenceSide(sizeOf(modelBounds));
  const maxExtra = structuralSide * (1 / MIN_ELEMENT_SHARE - 1);

  for (const shape of annotations) {
    for (const point of boundsPoints(shape, side)) {
      if (!isFinitePoint(point)) continue;
      modelBounds = extend(modelBounds, [[
        clampNear(point[0], modelBounds.minX, modelBounds.maxX, maxExtra),
        clampNear(point[1], modelBounds.minY, modelBounds.maxY, maxExtra),
      ]]);
    }
  }
  // M5 composition: re-centre the (possibly annotation-skewed) box on the STRUCTURAL element's
  // own centre -- an arrow/label reaching further on one side than the other must never shift the
  // drawing itself off-centre in its figure. A SMALL fraction of finding C1's own per-side
  // annotation budget (`maxExtra`), not the whole thing: `centerAround`'s `grow()` never shrinks a
  // side (so it can never clip content the annotation clamp already made room for), but the FULL
  // C1 budget on top of an already-clamped box measurably eats into "the element keeps >=60% of
  // the frame" on views the annotations already used most of that budget on one side alone
  // (measured: muro-sostegno/fond-plinto/neve-accumulo's dimension lines + labels) -- a twentieth
  // of it is enough to bring every measured view within the 10% centring target without doing that.
  modelBounds = centerAround(structuralBounds, modelBounds, maxExtra * CENTER_BUDGET_SHARE);

  const screenBounds = extend(null, [
    toScreen([modelBounds.minX, modelBounds.minY]),
    toScreen([modelBounds.maxX, modelBounds.maxY]),
  ]);
  const size = sizeOf(screenBounds);
  if (!(size.w > MIN_EXTENT) || !(size.h > MIN_EXTENT)) return null;

  const padX = size.w * padding;
  const padY = size.h * padding;

  // Finding C3: fixed screen-space margin for the longest label/text in the view, converted to
  // model units at an ASSUMED render width (the sketch renderer's own fallback box, close to
  // every real usage -- a few hundred px, Sintesi or full-size) -- close enough for a margin whose
  // only job is "big enough that text is never clipped", not an exact fit. Split X/Y, not one
  // uniform margin on every side: text is wide but SHORT (one line, `sketch-shapes.js`'s constant
  // 11.5px), so reserving its full width vertically too once inflated a naturally flat/wide view
  // (a roof line with one long label) well past finding C1's 60% element-share target for no
  // reason -- the text only ever needs that much clearance along its OWN horizontal axis.
  // Review finding 9: a vertical quota's text (sketch-shapes.js buildDimension) is anchored to ONE
  // side of its line rather than centred on it -- it can reach the line's FULL text width away
  // from it (anchor + full string), not just half, so the margin this fitter reserves must match
  // whenever the view has at least one such quota. Horizontal-only views keep the tighter half-
  // width margin: symmetric centred text never needed the extra room.
  const hasVerticalDimension = vista.forme.some((shape) => {
    if (!shape || shape.kind !== "dimension") return false;
    const { o1, o2 } = dimensionOffset(shape);
    return Math.abs(o2[1] - o1[1]) > Math.abs(o2[0] - o1[0]);
  });
  const labelMarginXPx = hasVerticalDimension
    ? longestTextPx(vista.forme) + LABEL_GAP_PX
    : longestTextPx(vista.forme) / 2 + LABEL_GAP_PX;
  const labelMarginYPx = TEXT_PX * 1.3 + LABEL_GAP_PX;
  // First pass: the heuristic above, the same on both sides of an axis (nothing is drawn yet, so
  // nobody knows where the text really ends up). Second pass (`marginsPx`, measured off the first
  // drawing by sketch-measure.js): what each side really needs -- a view whose only wide text
  // hangs off ONE side no longer gives away the same width on the other.
  const margins = marginsPx
    ? balancedMargins(marginsPx, box)
    : { left: labelMarginXPx, right: labelMarginXPx, top: labelMarginYPx, bottom: labelMarginYPx };
  const content = { minX: screenBounds.minX - padX, minY: screenBounds.minY - padY, w: size.w + 2 * padX, h: size.h + 2 * padY };
  const scale = marginAwareScale(content, margins, box);

  const minX = content.minX - margins.left / scale;
  const minY = content.minY - margins.top / scale;
  const width = content.w + (margins.left + margins.right) / scale;
  const height = content.h + (margins.top + margins.bottom) / scale;

  return {
    minX: round6(minX),
    minY: round6(minY),
    width: round6(width),
    height: round6(height),
    content, // the padded drawing box WITHOUT text margins (viewBox units): sketch-measure.js measures text overhang against it
    side, // kept in sync with the diagram's own render-time amplitude (sketch-shapes.js buildDiagram)
    viewBox: `${round6(minX)} ${round6(minY)} ${round6(width)} ${round6(height)}`,
  };
}

// -- M2: dimension-line minimum offset + stacking ------------------------------------------
// Authors give `Quota.distanza` in MODEL METRES (sketch.py COMPOSITION RULE 3: "6-8% of the
// view's larger side"); at a small enough scale that can still land only a few SCREEN px from the
// segment it measures, or two unrelated quotas can end up close enough to visually merge into one
// line. Both are renderer-side safety nets, not an authoring contract change -- they only ever
// GROW an offset that was already too small, never shrink one that was fine.
export const MIN_DIMENSION_OFFSET_PX = 22;
export const DIMENSION_STACK_PX = 18;
const PARALLEL_TOLERANCE = 0.05; // sin of the angle between two "parallel enough" directions
// Finding C1 caps how far an ANNOTATION may push the box open (`maxExtra`, MIN_ELEMENT_SHARE);
// the minimum-offset enforcement needs the same kind of ceiling -- otherwise a small element
// rendered at a small scale could have its 22px minimum expand to dominate the whole figure,
// undoing C1's "the element keeps >=60% of the frame" guarantee from the other direction. Well-
// authored offsets (sketch.py COMPOSITION RULE 3: "6-8% of the view's larger side") never get
// close to this; it only ever bites the pathological case the enforcement itself targets.
const MAX_DIMENSION_OFFSET_SHARE = 0.35;

function direction(p1, p2) {
  const dx = p2[0] - p1[0], dy = p2[1] - p1[1];
  const len = Math.hypot(dx, dy);
  return len > MIN_EXTENT ? { ux: dx / len, uy: dy / len, len } : null;
}

// True when two dimension lines run parallel (or anti-parallel) within `PARALLEL_TOLERANCE` AND
// their spans overlap once `b` is projected onto `a`'s own direction -- e.g. two quotas placed
// along the same footing edge, not two unrelated dimensions that merely happen to share a side.
function parallelAndOverlapping(a, b) {
  const da = direction(a.p1, a.p2);
  const db = direction(b.p1, b.p2);
  if (!da || !db) return false;
  if (Math.abs(da.ux * db.uy - da.uy * db.ux) > PARALLEL_TOLERANCE) return false;
  const proj = (p) => (p[0] - a.p1[0]) * da.ux + (p[1] - a.p1[1]) * da.uy;
  const lo = Math.min(proj(b.p1), proj(b.p2));
  const hi = Math.max(proj(b.p1), proj(b.p2));
  return lo < da.len && hi > 0;
}

// A dimension measured along a diagram's own base, on the side the diagram hangs from (the width B
// of a wall footing under its base-pressure diagram), must clear the WHOLE envelope plus the
// diagram's own end labels -- and only the renderer knows the envelope's depth (`altezza_relativa`
// of the view's reference side, not of anything a sketch author can compute: muro-sostegno's author
// estimated it from min(B, H) and the dimension landed inside the hatching). 0 when no diagram is
// in the way. Deliberately NOT subject to the C1 share cap: drawing over the diagram is worse.
const DIAGRAM_LABEL_PX = TEXT_PX * 1.3 + LABEL_GAP_PX;

function leftNormal(p1, p2) {
  const d = direction(p1, p2);
  return d ? [-d.uy, d.ux] : null;
}

function diagramClearance(quota, diagrams, referenceSide, scale) {
  const quotaNormal = leftNormal(quota.p1, quota.p2);
  if (!quotaNormal || !(referenceSide > 0)) return 0;
  const quotaSign = quota.distanza < 0 ? -1 : 1;
  return diagrams.reduce((needed, diagram) => {
    const base = { p1: diagram.base[0], p2: diagram.base[1] };
    const baseNormal = leftNormal(base.p1, base.p2);
    if (!baseNormal || !parallelAndOverlapping(quota, base)) return needed;
    const peak = diagram.valori.reduce((best, v) => (Math.abs(v) > Math.abs(best) ? v : best), 0);
    const sameSide = (quotaNormal[0] * baseNormal[0] + quotaNormal[1] * baseNormal[1]) * quotaSign * Math.sign(peak) > 0;
    if (!sameSide) return needed;
    const hasLabels = (diagram.etichette ?? []).some(Boolean);
    const clearance = diagram.altezza_relativa * referenceSide + (MIN_DIMENSION_OFFSET_PX + (hasLabels ? DIAGRAM_LABEL_PX : 0)) / scale;
    return Math.max(needed, clearance);
  }, 0);
}

// Returns a NEW array of `Quota`-shaped objects (never mutates the input): first every offset is
// grown, sign kept, to at least `MIN_DIMENSION_OFFSET_PX` screen px (converted to model units via
// `scale`, capped at `MAX_DIMENSION_OFFSET_SHARE` of `referenceSide` so it can never swamp a small
// element); then any pair left coincident (same side, overlapping spans, offsets still within one
// stacking step of each other) is pushed `DIMENSION_STACK_PX` further apart, later shapes
// stacking outward past earlier ones already resolved.
export function resolveDimensionOffsets(quotas, scale, referenceSide, diagrams = []) {
  const s = Math.max(scale, MIN_EXTENT);
  const cap = referenceSide > 0 ? referenceSide * MAX_DIMENSION_OFFSET_SHARE : Infinity;
  const minOffset = Math.min(MIN_DIMENSION_OFFSET_PX / s, cap);
  const stackStep = Math.min(DIMENSION_STACK_PX / s, cap);
  const resolved = quotas.map((shape) => {
    const sign = shape.distanza < 0 ? -1 : 1;
    const beyondDiagram = diagramClearance(shape, diagrams, referenceSide, s);
    return { ...shape, distanza: sign * Math.max(Math.abs(shape.distanza), minOffset, beyondDiagram) };
  });
  for (let i = 0; i < resolved.length; i++) {
    for (let j = 0; j < i; j++) {
      const a = resolved[i], b = resolved[j];
      if (Math.sign(a.distanza) !== Math.sign(b.distanza)) continue;
      if (Math.abs(Math.abs(a.distanza) - Math.abs(b.distanza)) >= stackStep) continue;
      if (!parallelAndOverlapping(a, b)) continue;
      const sign = a.distanza < 0 ? -1 : 1;
      resolved[i] = { ...a, distanza: sign * (Math.abs(b.distanza) + stackStep) };
    }
  }
  return resolved;
}

// Replaces every `dimension` shape in `forme` with its M2-adjusted counterpart at the given
// scale (`referenceSide`: the view's own reference side, for the C1 share cap above); every other
// shape passes through unchanged. Pure -- called twice on purpose (an approximate scale while
// fitting the viewBox, the real render scale while drawing), so the fitted box and the drawn
// geometry can never disagree about how big an enforced offset is.
export function applyDimensionOffsets(forme, scale, referenceSide) {
  const quotas = forme.filter((s) => s && s.kind === "dimension");
  if (quotas.length === 0) return forme;
  const diagrams = forme.filter((s) => s && s.kind === "diagram" && Array.isArray(s.base) && Array.isArray(s.valori));
  const resolved = resolveDimensionOffsets(quotas, scale, referenceSide, diagrams);
  const byShape = new Map(quotas.map((shape, i) => [shape, resolved[i]]));
  return forme.map((s) => (s && s.kind === "dimension" ? byShape.get(s) : s));
}

// Uniform px-per-model-unit for a fitted view rendered into a boxPx {width,height} container
// ("contain" fit, matching the viewBox's own default preserveAspectRatio behaviour).
export function uniformScale(view, boxPx) {
  if (!view || !boxPx || !(boxPx.width > 0) || !(boxPx.height > 0) || !(view.width > 0) || !(view.height > 0)) {
    return 1;
  }
  return Math.min(boxPx.width / view.width, boxPx.height / view.height);
}
