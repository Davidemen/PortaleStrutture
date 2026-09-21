// Generic renderer for `Sketch` (src/strutture/shared/sketch.py), WORKBENCH_SPEC.md #5.
// Public API: renderSketch(container, sketch, {previous} = {}) -> void.
// One <figure> per Vista, SVG viewBox fitted by sketch-fit.js, shapes drawn by sketch-shapes.js.
// Never throws: degenerate/invalid input renders nothing. The <figure>/<svg> identity is kept
// per view index when `previous` has the same title + shape-kind sequence, so a live re-render
// never removes/re-inserts the figure the user is looking at (no flicker, no re-mount).
import { el, clear } from "./dom.js";
import { fitVista, uniformScale, applyDimensionOffsets } from "./sketch-fit.js";
import { svgNode, buildShape, buildArrowMarkers, buildTerrenoPattern } from "./sketch-shapes.js";
import { resolveLabelCollisions } from "./sketch-labels.js";
import { measureTextOverhang, hasClippedText } from "./sketch-measure.js";

const FALLBACK_BOX_PX = 320;
const MAX_VIEWS = 4;

function structureKey(vista) {
  if (!vista || !Array.isArray(vista.forme)) return "";
  return `${vista.titolo ?? ""}|${vista.forme.map((f) => f?.kind ?? "?").join(",")}`;
}

function ariaLabel(vista, nota) {
  return [vista?.titolo ?? "", nota ?? ""].filter(Boolean).join(". ");
}

function buildFigure() {
  const figcaption = el("figcaption");
  const svg = svgNode("svg", { class: "sk-svg", role: "img" });
  const figure = el("figure", { class: "sk-figure" }, [figcaption, svg]);
  return { figure, figcaption, svg };
}

function applyView(svg, view) {
  svg.setAttribute("viewBox", view.viewBox);
  svg.setAttribute("width", view.width.toFixed(4));
  svg.setAttribute("height", view.height.toFixed(4));
}

// The box the svg REALLY got, or null when it is not laid out (a hidden print document). The
// height only counts as a constraint when CSS clamps it independently of the width (the Sintesi's
// min/max-height band): under plain `height:auto` it just follows the viewBox's own aspect ratio,
// and feeding it back into the fit would be circular.
const ASPECT_TOLERANCE = 0.02;

function realBox(svg, firstView) {
  const rect = svg.getBoundingClientRect();
  if (!(rect.width > 0) || !(rect.height > 0)) return null;
  const ownRatio = firstView.height / firstView.width;
  const heightClamped = Math.abs(rect.height / rect.width - ownRatio) > ownRatio * ASPECT_TOLERANCE;
  return { width: rect.width, height: heightClamped ? rect.height : 0 };
}

function refit(vista, options) {
  try {
    return fitVista(vista, options);
  } catch {
    return null;
  }
}

// Up to three drawings of the same view, each cheap (a few dozen nodes):
//  1. `firstView` was fitted for a nominal box (sketch-fit.js FALLBACK_BOX_WIDTH_PX) -- re-fit for
//     the real one: a half-width figure needs about twice the margin in model units for the same
//     11.5px text. Drawn with the fitter's HEURISTIC text margins (the longest text, both sides).
//  2. Measure how far the text really sticks out on each side (sketch-measure.js) and fit again
//     with exactly that -- typically a much larger drawing (neve-accumulo: margins went from 56%
//     of the figure's width to what its one left-hand dimension text needs).
//  3. Safety net: if the tight fit clipped any text after all, the heuristic drawing comes back.
function renderVista(svg, vista, firstView, viewIndex, idPrefix) {
  applyView(svg, firstView);
  const boxPx = realBox(svg, firstView);
  const loose = (boxPx && refit(vista, { boxPx })) || firstView;
  drawVistaAt(svg, vista, loose, viewIndex, idPrefix);
  if (!boxPx) return;
  const marginsPx = measureTextOverhang(svg, loose);
  const tight = marginsPx ? refit(vista, { boxPx, marginsPx }) : null;
  if (!tight) return;
  drawVistaAt(svg, vista, tight, viewIndex, idPrefix);
  if (hasClippedText(svg)) drawVistaAt(svg, vista, loose, viewIndex, idPrefix);
}

function drawVistaAt(svg, vista, view, viewIndex, idPrefix) {
  applyView(svg, view);
  // Measured on the svg itself (already attached to the document at this point), not on the
  // caller's container: a CSS max-width on .sk-figure (or any ancestor) can make the two differ,
  // and only the svg's own rendered box determines how many CSS px a viewBox unit really is.
  // BOTH dimensions are read directly off the live box -- deriving height from
  // `width * (view.height/view.width)` (assuming CSS `height:auto`) undercounts/overcounts scale
  // whenever a container clamps height independently of width, e.g. the Sintesi's own
  // `.r-si-sketch .sk-figure { min-height:220px; max-height:320px }` + `.sk-svg { height:100% }`:
  // there the box's real aspect ratio routinely does NOT match the view's, so
  // `preserveAspectRatio="meet"` (default) letterboxes on whichever axis is actually the tighter
  // fit -- and only measuring both axes catches that (M2's minimum dimension offset depends on
  // this being right: a wrong, too-large assumed scale under-boosts the offset).
  const rect = svg.getBoundingClientRect();
  const boxPx = {
    width: rect.width > 0 ? rect.width : FALLBACK_BOX_PX,
    height: rect.height > 0 ? rect.height : FALLBACK_BOX_PX * (view.height / view.width),
  };
  const s = uniformScale(view, boxPx);
  clear(svg);
  // M2: re-apply the min-offset/stacking adjustment at the REAL render scale (fitVista already
  // did it once at an approximate scale, purely to size the viewBox) -- same pure transform, so
  // the drawn dimension lines always match or exceed what the viewBox was fitted for.
  const forme = applyDimensionOffsets(vista.forme, s, view.side);
  const hasArrow = forme.some((f) => f?.kind === "arrow");
  const hasTerreno = forme.some((f) => f?.stile === "terreno");
  if (hasArrow || hasTerreno) {
    const defs = svgNode("defs");
    if (hasArrow) defs.append(...buildArrowMarkers(viewIndex, s, idPrefix));
    if (hasTerreno) defs.append(buildTerrenoPattern(viewIndex, s, idPrefix));
    svg.append(defs);
  }
  const ctx = { s, side: view.side, viewIndex, idPrefix };
  for (const shape of forme) {
    try {
      const node = buildShape(shape, ctx);
      if (node) svg.append(node);
    } catch {
      // one malformed shape must never take down the whole sketch (input validation: never
      // trust the network payload's shape even though the server already validated it).
    }
  }
  // Finding C2: nudge overlapping labels apart now that every shape (and its text) is in the
  // live DOM and measurable. Never allowed to break the sketch itself.
  try {
    resolveLabelCollisions(svg);
  } catch {
    // best-effort only -- a mis-measured label is far better than a broken sketch.
  }
}

export function renderSketch(container, sketch, { previous, idPrefix = "" } = {}) {
  if (!container) return;
  // M6: `Sketch.nota` ("Schema non in scala") as a small caption under the views -- pulled out
  // before the per-view diffing below (which assumes every child of `container` is a view
  // figure) and re-appended fresh at the end, so its presence never throws off the view reuse-by-
  // index logic. Already in every view's own `aria-label` (`ariaLabel` below); this is the
  // additional VISIBLE caption.
  const previousNota = container.querySelector(":scope > .sk-nota");
  if (previousNota) previousNota.remove();
  if (!sketch || !Array.isArray(sketch.viste) || sketch.viste.length === 0) {
    clear(container);
    return;
  }
  const views = sketch.viste.slice(0, MAX_VIEWS);
  const prevViews = Array.isArray(previous?.viste) ? previous.viste : [];
  const existing = Array.from(container.children);
  // Two passes on purpose: EVERY figure is mounted before ANY view is measured and drawn. The
  // container's own layout depends on how many figures it holds (results.css switches
  // `.r-si-sketch` to a two-column grid once a second figure exists), so drawing view 0 while it
  // was still the only child sized its text/offsets for a full-width box that halved a moment
  // later -- every first view ("Pianta") ended up with half-size text and sub-minimum dimension
  // offsets next to a correctly-sized second view.
  const mounted = [];

  views.forEach((vista, index) => {
    if (!vista || !Array.isArray(vista.forme)) return;
    let view;
    try {
      view = fitVista(vista);
    } catch {
      view = null;
    }
    if (!view) return;

    const reuse = existing[index] && structureKey(vista) === structureKey(prevViews[index]);
    let figure, svg, figcaption;
    if (reuse) {
      figure = existing[index];
      svg = figure.querySelector("svg");
      figcaption = figure.querySelector("figcaption");
    } else {
      ({ figure, svg, figcaption } = buildFigure());
      if (existing[index]) existing[index].replaceWith(figure);
      else container.append(figure);
    }
    figcaption.textContent = vista.titolo ?? "";
    svg.setAttribute("aria-label", ariaLabel(vista, sketch.nota));
    mounted.push({ svg, vista, view, index });
  });

  while (container.children.length > views.length) {
    container.lastElementChild.remove();
  }

  if (sketch.nota) container.append(el("p", { class: "sk-nota", text: sketch.nota }));

  const draw = () => mounted.forEach(({ svg, vista, view, index }) => drawVista(svg, vista, view, index, idPrefix));
  draw();
  redrawOnResize(container, draw);
}

function drawVista(svg, vista, view, index, idPrefix) {
  try {
    renderVista(svg, vista, view, index, idPrefix);
  } catch {
    clear(svg);
  }
}

// Text and dimension offsets are sized in SCREEN px at draw time, so a container that changes
// width afterwards (rail collapsed/expanded, window resized, Sintesi column reflow) needs a
// re-draw at the new scale -- otherwise the labels scale with the drawing. One observer per
// container, always calling the LATEST draw closure; it disconnects itself once the container
// leaves the document (live calculation rebuilds the Sintesi, and with it this container).
const RESIZE_TOLERANCE_PX = 1;
const resizeState = new WeakMap();

function redrawOnResize(container, draw) {
  if (typeof ResizeObserver !== "function") return;
  const state = resizeState.get(container);
  if (state) {
    state.draw = draw;
    return;
  }
  const fresh = { draw, width: container.getBoundingClientRect().width };
  const observer = new ResizeObserver((entries) => {
    if (!container.isConnected) {
      observer.disconnect();
      resizeState.delete(container);
      return;
    }
    const width = entries[entries.length - 1].contentRect.width;
    if (!(width > 0) || Math.abs(width - fresh.width) <= RESIZE_TOLERANCE_PX) return;
    fresh.width = width;
    fresh.draw();
  });
  resizeState.set(container, fresh);
  observer.observe(container);
}
