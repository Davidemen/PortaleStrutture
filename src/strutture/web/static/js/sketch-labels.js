// Screen-space label collision avoidance for the sketch renderer (WORKBENCH_SPEC #5, finding C2 +
// M5): "measure label boxes in screen space and nudge overlapping ones apart" (max 4 passes).
// Runs AFTER a view's shapes are already in the live DOM (sketch.js), since it needs real
// `getBoundingClientRect()` measurements -- there is no way to know two labels overlap from
// model-space coordinates alone (font metrics, the view's actual on-screen scale, ...). Each
// overlapping pair is pushed apart along whichever axis needs LESS movement to clear (the
// standard minimum-translation-vector heuristic) -- vertical-only nudging left some pairs
// (an arrow-tip label beside another at nearly the same height) still overlapping.
const MAX_PASSES = 4;
const MIN_NUDGE_PX = 4;
const LEADER_THRESHOLD_PX = 14; // M5: a label nudged further than this needs a leader back to its anchor
const SVG_NS = "http://www.w3.org/2000/svg";

// Every text-bearing group the shape builders emit (sketch-shapes.js `textAt`): dimension/label/
// arrow/diagram text, each wrapped in its own `<g transform="translate(x y) scale(1/s)">`.
function textGroups(svg) {
  return Array.from(svg.querySelectorAll(".sk-quota-text, .sk-diagram-text, .sk-label, .sk-arrow-text")).filter(
    (node) => node.tagName === "g"
  );
}

function rectsOverlap(a, b) {
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}

function currentTranslate(group) {
  const match = /translate\(([-\d.eE+]+)[ ,]([-\d.eE+]+)\)/.exec(group.getAttribute("transform") || "");
  return match ? { x: Number(match[1]), y: Number(match[2]) } : null;
}

// viewBox units per screen px. ONE ratio for both axes: the svg scales uniformly ("meet"), so in a
// box whose aspect ratio differs from the viewBox's (the Sintesi clamps the figure's height) the
// slack axis is letterboxed, not stretched -- a per-axis width/height ratio over-nudged along it.
function unitsPerPx(svg) {
  const viewBox = svg.viewBox.baseVal;
  const rect = svg.getBoundingClientRect();
  if (!viewBox || !(rect.width > 0) || !(rect.height > 0) || !(viewBox.width > 0) || !(viewBox.height > 0)) return null;
  return Math.max(viewBox.width / rect.width, viewBox.height / rect.height);
}

// Moves a label group by `dxPx`/`dyPx` CSS pixels ON SCREEN, converting through the svg's own
// viewBox-unit-to-screen-px ratio (per axis) so the nudge looks the same regardless of the view's
// scale or aspect ratio.
function nudgeScreen(svg, group, dxPx, dyPx) {
  const ratio = unitsPerPx(svg);
  if (!ratio) return;
  const match = /translate\(([-\d.eE+]+)[ ,]([-\d.eE+]+)\)\s*scale\(([-\d.eE+]+)\)/.exec(group.getAttribute("transform") || "");
  if (!match) return;
  const x = Number(match[1]) + dxPx * ratio;
  const y = Number(match[2]) + dyPx * ratio;
  const s = match[3];
  group.setAttribute("transform", `translate(${x.toFixed(4)} ${y.toFixed(4)}) scale(${s})`);
}

// M5: once collision avoidance has moved a label more than `LEADER_THRESHOLD_PX` (either axis)
// from where it would otherwise have sat, draw a thin line back to that original anchor point --
// both ends are already in viewBox/user units (the group's own `translate`), so no further
// conversion is needed to draw it; only the >14px THRESHOLD decision needs the screen-px ratio.
function addLeaderLines(svg, groups, originals) {
  const ratio = unitsPerPx(svg);
  if (!ratio) return;
  groups.forEach((group, i) => {
    const before = originals[i];
    const after = currentTranslate(group);
    if (!before || !after) return;
    const movedPx = Math.hypot(after.x - before.x, after.y - before.y) / ratio;
    if (movedPx <= LEADER_THRESHOLD_PX) return;
    const leader = document.createElementNS(SVG_NS, "line");
    leader.setAttribute("class", "sk-leader");
    leader.setAttribute("x1", before.x.toFixed(4));
    leader.setAttribute("y1", before.y.toFixed(4));
    leader.setAttribute("x2", after.x.toFixed(4));
    leader.setAttribute("y2", after.y.toFixed(4));
    leader.setAttribute("vector-effect", "non-scaling-stroke");
    svg.insertBefore(leader, group);
  });
}

// Mutates `svg` in place: up to MAX_PASSES rounds of "measure every label box, and for each
// overlapping pair push them apart along the axis that clears them with less movement". Never
// throws -- a failed measurement (e.g. a detached svg) just leaves labels where they were.
export function resolveLabelCollisions(svg) {
  let groups;
  try {
    groups = textGroups(svg);
  } catch {
    return;
  }
  if (groups.length < 2) return;
  const originals = groups.map((group) => currentTranslate(group));

  for (let pass = 0; pass < MAX_PASSES; pass++) {
    let boxes;
    try {
      boxes = groups.map((group) => group.getBoundingClientRect());
    } catch {
      return;
    }
    let moved = false;
    for (let i = 0; i < groups.length; i++) {
      for (let j = i + 1; j < groups.length; j++) {
        if (!rectsOverlap(boxes[i], boxes[j])) continue;
        const overlapX = Math.min(boxes[i].right, boxes[j].right) - Math.max(boxes[i].left, boxes[j].left);
        const overlapY = Math.min(boxes[i].bottom, boxes[j].bottom) - Math.max(boxes[i].top, boxes[j].top);
        const step = Math.max(Math.min(overlapX, overlapY) / 2 + 2, MIN_NUDGE_PX);
        if (overlapX <= overlapY) {
          const sign = boxes[i].left <= boxes[j].left ? -1 : 1;
          nudgeScreen(svg, groups[i], sign * step, 0);
          nudgeScreen(svg, groups[j], -sign * step, 0);
        } else {
          const sign = boxes[i].top <= boxes[j].top ? -1 : 1;
          nudgeScreen(svg, groups[i], 0, sign * step);
          nudgeScreen(svg, groups[j], 0, -sign * step);
        }
        moved = true;
      }
    }
    if (!moved) break;
  }

  try {
    addLeaderLines(svg, groups, originals);
  } catch {
    // best-effort, same as the nudging above -- a missing leader line is cosmetic only.
  }
}
