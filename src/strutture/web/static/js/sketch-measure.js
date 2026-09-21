// Measures a DRAWN sketch view: how far its text sticks out past the drawing itself, per side, in
// screen px -- and whether any text ended up outside the svg's own box. Text is drawn at a constant
// on-screen size (sketch-shapes.js textAt), so its real extent is only knowable after drawing;
// sketch.js feeds these numbers back into sketch-fit.js for a second, tighter fit.
// Pure reads of the live DOM: never mutates the svg, returns null whenever it cannot measure (not
// laid out, no CTM) so the caller simply keeps its first, heuristic fit.
import { LABEL_GAP_PX } from "./sketch-text.js";

const CLIP_TOLERANCE_PX = 1;

function textRects(svg) {
  return Array.from(svg.querySelectorAll("text"))
    .map((node) => node.getBoundingClientRect())
    .filter((rect) => rect.width > 0 && rect.height > 0);
}

// `view.content` (sketch-fit.js fitVista) is the padded drawing box in viewBox units.
function contentRectPx(svg, view) {
  const ctm = typeof svg.getScreenCTM === "function" ? svg.getScreenCTM() : null;
  if (!ctm || !view?.content) return null;
  const corner = (x, y) => {
    const point = svg.createSVGPoint();
    point.x = x;
    point.y = y;
    return point.matrixTransform(ctm);
  };
  const a = corner(view.content.minX, view.content.minY);
  const b = corner(view.content.minX + view.content.w, view.content.minY + view.content.h);
  return { left: Math.min(a.x, b.x), right: Math.max(a.x, b.x), top: Math.min(a.y, b.y), bottom: Math.max(a.y, b.y) };
}

function overhang(distancePx) {
  return distancePx > 0 ? distancePx + LABEL_GAP_PX : 0;
}

// {left, right, top, bottom} px the text needs beyond the drawing box; all zero when every text
// sits inside it. Measured at the CURRENT scale: a tighter second fit only ever draws larger, which
// moves interior labels further inside -- so these numbers stay a safe upper bound.
export function measureTextOverhang(svg, view) {
  const content = contentRectPx(svg, view);
  if (!content) return null;
  return textRects(svg).reduce(
    (acc, rect) => ({
      left: Math.max(acc.left, overhang(content.left - rect.left)),
      right: Math.max(acc.right, overhang(rect.right - content.right)),
      top: Math.max(acc.top, overhang(content.top - rect.top)),
      bottom: Math.max(acc.bottom, overhang(rect.bottom - content.bottom)),
    }),
    { left: 0, right: 0, top: 0, bottom: 0 },
  );
}

// True when any drawn text crosses the svg's own box (it would be clipped by the figure).
export function hasClippedText(svg) {
  const box = svg.getBoundingClientRect();
  if (!(box.width > 0) || !(box.height > 0)) return false;
  return textRects(svg).some(
    (rect) =>
      rect.left < box.left - CLIP_TOLERANCE_PX ||
      rect.right > box.right + CLIP_TOLERANCE_PX ||
      rect.top < box.top - CLIP_TOLERANCE_PX ||
      rect.bottom > box.bottom + CLIP_TOLERANCE_PX,
  );
}
