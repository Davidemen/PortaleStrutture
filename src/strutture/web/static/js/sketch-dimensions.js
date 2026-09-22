// M2: dimension-line minimum offset + stacking. Split out of sketch-fit.js (WORKBENCH_SPEC.md
// §22, module cap): code moved verbatim. Authors give `Quota.distanza` in MODEL METRES (sketch.py
// COMPOSITION RULE 3: "6-8% of the view's larger side"); at a small enough scale that can still
// land only a few SCREEN px from the segment it measures, or two unrelated quotas can end up close
// enough to visually merge into one line. Both are renderer-side safety nets, not an authoring
// contract change -- they only ever GROW an offset that was already too small, never shrink one
// that was fine.
import { MIN_EXTENT } from "./sketch-geometry.js";
import { TEXT_PX, LABEL_GAP_PX } from "./sketch-text.js";

export const MIN_DIMENSION_OFFSET_PX = 22;
export const DIMENSION_STACK_PX = 18;
const PARALLEL_TOLERANCE = 0.05; // sin of the angle between two "parallel enough" directions
// Finding C1 caps how far an ANNOTATION may push the box open (`maxExtra`, MIN_ELEMENT_SHARE in
// sketch-fit.js); the minimum-offset enforcement needs the same kind of ceiling -- otherwise a
// small element rendered at a small scale could have its 22px minimum expand to dominate the whole
// figure, undoing C1's "the element keeps >=60% of the frame" guarantee from the other direction.
// Well-authored offsets (sketch.py COMPOSITION RULE 3: "6-8% of the view's larger side") never get
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
// scale (`referenceSide`: the view's own reference side, for the C1 share cap in sketch-fit.js);
// every other shape passes through unchanged. Pure -- called twice on purpose (an approximate
// scale while fitting the viewBox, the real render scale while drawing), so the fitted box and the
// drawn geometry can never disagree about how big an enforced offset is.
export function applyDimensionOffsets(forme, scale, referenceSide) {
  const quotas = forme.filter((s) => s && s.kind === "dimension");
  if (quotas.length === 0) return forme;
  const diagrams = forme.filter((s) => s && s.kind === "diagram" && Array.isArray(s.base) && Array.isArray(s.valori));
  const resolved = resolveDimensionOffsets(quotas, scale, referenceSide, diagrams);
  const byShape = new Map(quotas.map((shape, i) => [shape, resolved[i]]));
  return forme.map((s) => (s && s.kind === "dimension" ? byShape.get(s) : s));
}
