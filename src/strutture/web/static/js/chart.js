// Inline SVG line chart for row-tuple outputs (spectrum, wind profile, ...).
// Contract: renderChart(container, {rows, chart, series, labels, guides}) -> SVGElement|null.
// `chart` = the backend hint {x, x_label, y[], y_label, guides?}; `series` = [{key,label,symbol,className}].
// No inline style attribute is ever set on the SVG: colour comes from CSS classes + currentColor,
// geometry from SVG presentation attributes. The pointer/keyboard tooltip is a plain HTML overlay.

import { svgEl, niceTicks, scale, formatTick, buildYAxis, buildXAxis, buildGuide, buildHGuide } from "./chart-axis.js";
import { symbolTspans } from "./symbols.js";

// Below 720px (layout.css breakpoint) a narrower, shorter viewBox keeps the SVG-to-viewport
// scale close to 1:1 -- the wide 640x320 desktop box, shrunk to a ~300px-wide mobile column,
// scaled every CSS px (including tick-label font-size) down with it, to the ~7px the review flagged.
const NARROW_MEDIA_QUERY = "(max-width: 719.98px)";
const DESKTOP_VB = { w: 640, h: 320, margin: { top: 28, right: 104, bottom: 34, left: 52 } };
const NARROW_VB = { w: 340, h: 200, margin: { top: 22, right: 70, bottom: 32, left: 44 } };
const MAX_POINTS = 400;
// Minimum vertical gap (in viewBox user units, ~= CSS px at the scales above) between two
// series' end points below which direct end-of-line labels would overlap; below it we rely on
// the legend instead (finding: "se_g"/"sd_g" overprinting where the spectrum curves converge).
const LABEL_MIN_GAP = 14;

function isNarrowViewport() {
  return typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia(NARROW_MEDIA_QUERY).matches;
}

// `yMax` (sensibilita.js's ETA_MAX_GRAFICO, WORKBENCH_SPEC §24.2): caps the y domain so one huge
// utilisation cannot flatten the rest of the curve -- points above it are clipped to the top edge
// and marked with a "▲" (the accessible table below always shows the true value). `hGuides`
// (`[{value, label}]`) draws a horizontal guide (the utilisation target) the same dashed style as
// the existing vertical `guides`, included in the (now possibly capped) y domain like a data value.
export function renderChart(container, { rows, chart, series, labels, guides, hGuides, yMax } = {}) {
  container.replaceChildren();
  if (!chart || !Array.isArray(rows) || !Array.isArray(series) || series.length === 0) {
    return null;
  }
  const { w: vbW, h: vbH, margin } = isNarrowViewport() ? NARROW_VB : DESKTOP_VB;
  const sampled = decimateRows(rows, MAX_POINTS);
  const xInfo = buildXValues(sampled, chart.x);
  const seriesData = series.map((s, i) => ({
    ...s,
    className: s.className ?? `c-series-${i + 1}`,
    points: sampled.map((row, i2) => ({ x: xInfo.values[i2], y: toFinite(row[s.key]) })),
  }));
  const validCount = Math.max(0, ...seriesData.map((s) => s.points.filter((p) => p.y !== null).length));
  if (validCount < 2) {
    return null;
  }

  const plot = { x0: margin.left, x1: vbW - margin.right, y0: vbH - margin.bottom, y1: margin.top };
  const xDomain = xInfo.numeric ? niceTicks(xInfo.min, xInfo.max, 5) : [0, xInfo.values.length - 1];
  const xScale = scale([xDomain[0], xDomain[xDomain.length - 1]], [plot.x0, plot.x1]);
  const rawYValues = seriesData.flatMap((s) => s.points.map((p) => p.y)).filter((v) => v !== null);
  const hGuideValues = (hGuides ?? []).map((g) => g.value).filter((v) => Number.isFinite(v));
  const yValues = [...rawYValues, ...hGuideValues];
  const yCeiling = Number.isFinite(yMax) ? Math.min(Math.max(...yValues), yMax) : Math.max(...yValues);
  const yTicks = niceTicks(Math.min(...yValues), yCeiling, 5);
  const yScale = scale([yTicks[0], yTicks[yTicks.length - 1]], [plot.y0, plot.y1]);
  const yTop = yTicks[yTicks.length - 1];

  const svg = svgEl("svg", {
    class: "c-svg",
    viewBox: `0 0 ${vbW} ${vbH}`,
    preserveAspectRatio: "xMidYMid meet",
    "aria-hidden": "true",
  });
  svg.append(buildYAxis(yTicks, plot, yScale, labels?.yLabel ?? chart.y_label));
  svg.append(buildXAxis(xInfo, xDomain, plot, xScale, labels?.xLabel ?? chart.x_label, vbH));
  for (const guide of guides ?? []) {
    if (Number.isFinite(guide.value)) svg.append(buildGuide(guide, xScale(guide.value), plot));
  }
  for (const guide of hGuides ?? []) {
    if (Number.isFinite(guide.value)) svg.append(buildHGuide(guide, Math.min(yScale(guide.value), plot.y0), plot));
  }
  const built = seriesData.map((s) => buildSeriesPath(s, xScale, yScale, yTop, plot.y1));
  appendDirectLabels(built);
  for (const b of built) svg.append(b.group);
  const crosshair = svgEl("line", { class: "c-crosshair", x1: plot.x0, x2: plot.x0, y1: plot.y1, y2: plot.y0, display: "none" });
  svg.append(crosshair);
  container.append(svg);
  if (seriesData.length >= 2) {
    container.append(buildLegend(seriesData));
  }
  const tooltip = buildTooltip(container);
  // The SVG stays `aria-hidden` (the table is the accessible alternative, DESIGN_SPEC §3); focus
  // and the arrow-key/tooltip interaction move to this wrapper instead, so nothing focusable is
  // ever hidden from assistive tech (a focusable+aria-hidden node traps keyboard users in a void).
  container.classList.add("c-chart-wrap");
  container.setAttribute("tabindex", "0");
  container.setAttribute("role", "img");
  const yLabel = labels?.yLabel ?? chart.y_label ?? "";
  const xLabel = labels?.xLabel ?? chart.x_label ?? "";
  container.setAttribute("aria-label", `Grafico: ${yLabel} in funzione di ${xLabel}; dati nella tabella sottostante`);
  attachInteraction(svg, container, plot, xScale, xInfo, seriesData, crosshair, tooltip, vbW);
  return svg;
}

function toFinite(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function decimateRows(rows, max) {
  if (rows.length <= max) return rows;
  const step = (rows.length - 1) / (max - 1);
  return Array.from({ length: max }, (_, i) => rows[Math.round(i * step)]);
}

function buildXValues(rows, xKey) {
  const raw = rows.map((r) => r[xKey]);
  const numeric = raw.every((v) => typeof v === "number" && Number.isFinite(v));
  if (numeric) {
    return { numeric: true, values: raw, min: Math.min(...raw), max: Math.max(...raw), labels: null };
  }
  return { numeric: false, values: raw.map((_, i) => i), labels: raw.map((v) => String(v)) };
}

// Builds the path only; the direct end-of-line label is decided afterwards, once every series'
// endpoint is known, so two converging curves can agree to fall back to the legend instead.
// `yTop`/`plotY1` (sensibilita.js's ETA_MAX_GRAFICO clip): a point whose y falls above the domain
// (its SVG y coordinate above `plotY1`) is drawn clipped to the top edge with a "▲" marker.
function buildSeriesPath(s, xScale, yScale, yTop, plotY1) {
  const g = svgEl("g", { class: s.className });
  let d = "";
  let drawing = false;
  let last = null;
  for (const p of s.points) {
    if (p.y === null) {
      drawing = false;
      continue;
    }
    const x = xScale(p.x);
    const clipped = Number.isFinite(yTop) && p.y > yTop;
    const y = clipped ? plotY1 : yScale(p.y);
    d += `${drawing ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)} `;
    drawing = true;
    last = { x, y };
    if (clipped) {
      const marker = svgEl("text", { class: "c-clip-marker", x, y: plotY1 + 4, "text-anchor": "middle" });
      marker.textContent = "▲";
      g.append(marker);
    }
  }
  g.append(svgEl("path", { d: d.trim(), fill: "none", stroke: "currentColor", "stroke-width": "2", "data-series": s.key }));
  return { group: g, series: s, last };
}

// Direct labels use the column SYMBOL (real <tspan> subscripts), never the raw field key, and
// only render when the series' endpoints are far enough apart vertically to stay legible; the
// legend (drawn separately, always present for >=2 series) is the fallback the spec calls for.
function appendDirectLabels(built) {
  for (const entry of built) {
    if (!entry.last || !hasClearGap(entry, built)) continue;
    const fullLabel = entry.series.label ?? entry.series.symbol ?? entry.series.key;
    const text = svgEl("text", { x: entry.last.x + 6, y: entry.last.y + 4, "text-anchor": "start" });
    if (entry.series.symbol) {
      text.append(...symbolTspans(entry.series.symbol));
    } else {
      text.textContent = fullLabel;
    }
    const title = svgEl("title");
    title.textContent = fullLabel;
    text.append(title);
    entry.group.append(text);
  }
}

function hasClearGap(entry, built) {
  return built.every((other) => other === entry || !other.last || Math.abs(other.last.y - entry.last.y) >= LABEL_MIN_GAP);
}

function buildLegend(seriesData) {
  const ul = document.createElement("ul");
  ul.className = "c-legend";
  for (const s of seriesData) {
    const li = document.createElement("li");
    li.className = s.className;
    const swatch = document.createElement("b");
    swatch.className = "c-legend-swatch";
    const span = document.createElement("span");
    span.className = "c-legend-label";
    span.textContent = s.label ?? s.key;
    li.append(swatch, span);
    ul.append(li);
  }
  return ul;
}

function buildTooltip(container) {
  const tip = document.createElement("div");
  tip.className = "c-tooltip";
  tip.hidden = true;
  container.append(tip);
  return tip;
}

function attachInteraction(svg, wrapper, plot, xScale, xInfo, seriesData, crosshair, tooltip, vbW) {
  const n = xInfo.values.length;
  let activeIndex = 0;

  const show = (index) => {
    activeIndex = Math.max(0, Math.min(n - 1, index));
    const x = xScale(xInfo.values[activeIndex]);
    crosshair.setAttribute("x1", x);
    crosshair.setAttribute("x2", x);
    crosshair.setAttribute("display", "");
    const xLabel = xInfo.numeric ? formatTick(xInfo.values[activeIndex]) : xInfo.labels[activeIndex];
    const lines = [xLabel, ...seriesData.map((s) => seriesLine(s, activeIndex)).filter(Boolean)];
    tooltip.replaceChildren(...lines.map((text) => Object.assign(document.createElement("p"), { textContent: text })));
    tooltip.hidden = false;
    const bounds = svg.getBoundingClientRect();
    tooltip.style.setProperty("--tt-x", `${(x / vbW) * bounds.width}px`);
  };
  const hide = () => {
    crosshair.setAttribute("display", "none");
    tooltip.hidden = true;
  };
  svg.addEventListener("pointermove", (event) => {
    const bounds = svg.getBoundingClientRect();
    const relX = ((event.clientX - bounds.left) / bounds.width) * vbW;
    show(Math.round(((relX - plot.x0) / (plot.x1 - plot.x0)) * (n - 1)));
  });
  svg.addEventListener("pointerleave", hide);
  wrapper.addEventListener("blur", hide);
  wrapper.addEventListener("keydown", (event) => {
    if (event.key === "ArrowRight") {
      show(activeIndex + 1);
      event.preventDefault();
    } else if (event.key === "ArrowLeft") {
      show(activeIndex - 1);
      event.preventDefault();
    } else if (event.key === "Escape") {
      hide();
    }
  });
}

function seriesLine(s, index) {
  const v = s.points[index]?.y;
  return v === null || v === undefined ? null : `${s.label ?? s.key}: ${formatTick(v)}`;
}
