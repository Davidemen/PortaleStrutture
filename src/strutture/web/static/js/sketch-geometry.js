// Pure geometry for the sketch renderer (WORKBENCH_SPEC.md #5, findings C1/C3): model-space bounds
// of a shape, the y-flip to screen space, and the small numeric helpers the fitter and the
// dimension-offset resolver both need. No DOM, no globals -- unit-testable with `node --test`.
// Model space: metres, y UP (src/strutture/shared/sketch.py). Screen/SVG space: y DOWN.
// Split out of sketch-fit.js (WORKBENCH_SPEC.md §22, module cap): code moved verbatim.
export const PADDING = 0.08;
export const MIN_EXTENT = 1e-6;

export function isFiniteNumber(n) {
  return typeof n === "number" && Number.isFinite(n);
}

export function isFinitePoint(p) {
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

export function extend(bounds, points) {
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

export function boundsOfShapes(forme, side) {
  let b = null;
  for (const shape of forme) b = extend(b, boundsPoints(shape, side));
  return b;
}

export function sizeOf(b) {
  return b ? { w: b.maxX - b.minX, h: b.maxY - b.minY } : { w: 0, h: 0 };
}

export function referenceSide(size) {
  if (size.w > MIN_EXTENT && size.h > MIN_EXTENT) return Math.min(size.w, size.h);
  return Math.max(size.w, size.h, MIN_EXTENT);
}

export function round6(n) {
  return Number(n.toFixed(6));
}
