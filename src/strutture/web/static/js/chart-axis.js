// Axis helpers for chart.js: nice round ticks, linear domain -> range scales,
// tick formatting and the SVG axis/guide groups themselves (kept here so chart.js
// stays focused on data prep, series paths and pointer/keyboard interaction).

export const SVG_NS = "http://www.w3.org/2000/svg";

export function svgEl(tag, attrs = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value !== undefined && value !== null) node.setAttribute(key, value);
  }
  return node;
}

export function niceTicks(min, max, count = 5) {
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return [0];
  }
  if (min === max) {
    return [min - 1, min, min + 1];
  }
  const span = niceNumber(max - min, false);
  const step = niceNumber(span / Math.max(1, count - 1), true);
  const niceMin = Math.floor(min / step) * step;
  const niceMax = Math.ceil(max / step) * step;
  const ticks = [];
  for (let v = niceMin; v <= niceMax + step / 2; v += step) {
    ticks.push(roundToStep(v, step));
  }
  return ticks;
}

function niceNumber(range, round) {
  if (range <= 0) return 1;
  const exponent = Math.floor(Math.log10(range));
  const fraction = range / 10 ** exponent;
  let niceFraction;
  if (round) {
    if (fraction < 1.5) niceFraction = 1;
    else if (fraction < 3) niceFraction = 2;
    else if (fraction < 7) niceFraction = 5;
    else niceFraction = 10;
  } else if (fraction <= 1) {
    niceFraction = 1;
  } else if (fraction <= 2) {
    niceFraction = 2;
  } else if (fraction <= 5) {
    niceFraction = 5;
  } else {
    niceFraction = 10;
  }
  return niceFraction * 10 ** exponent;
}

function roundToStep(value, step) {
  const decimals = Math.max(0, -Math.floor(Math.log10(step)) + 2);
  return Number(value.toFixed(decimals));
}

export function scale(domain, range) {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  if (d1 === d0) {
    const mid = (r0 + r1) / 2;
    return () => mid;
  }
  return (value) => r0 + ((value - d0) / (d1 - d0)) * (r1 - r0);
}

export function formatTick(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return String(value);
  }
  return value.toLocaleString("it-IT", { maximumSignificantDigits: 4 });
}

export function buildYAxis(ticks, plot, yScale, label) {
  const g = svgEl("g", { class: "c-axis c-axis-y" });
  for (const t of ticks) {
    const y = yScale(t);
    g.append(svgEl("line", { x1: plot.x0, x2: plot.x1, y1: y, y2: y }));
    const text = svgEl("text", { x: plot.x0 - 8, y: y + 3, "text-anchor": "end" });
    text.textContent = formatTick(t);
    g.append(text);
  }
  if (label) {
    // Above the top tick, left-aligned on the plot area -- not at the SVG's own x=0/y=12, which
    // collided with the highest y tick label.
    const caption = svgEl("text", { x: plot.x0, y: plot.y1 - 10, "text-anchor": "start" });
    caption.textContent = label;
    g.append(caption);
  }
  return g;
}

export function buildXAxis(xInfo, xDomain, plot, xScale, label, vbHeight) {
  const g = svgEl("g", { class: "c-axis c-axis-x" });
  g.append(svgEl("line", { x1: plot.x0, x2: plot.x1, y1: plot.y0, y2: plot.y0 }));
  const stride = Math.max(1, Math.ceil(xInfo.values.length / 8));
  const ticks = xInfo.numeric ? xDomain : xInfo.values.filter((_, i) => i % stride === 0);
  for (const t of ticks) {
    const x = xScale(t);
    const text = svgEl("text", { x, y: plot.y0 + 18, "text-anchor": "middle" });
    text.textContent = xInfo.numeric ? formatTick(t) : xInfo.labels[t];
    g.append(text);
  }
  if (label) {
    const caption = svgEl("text", { x: (plot.x0 + plot.x1) / 2, y: vbHeight - 4, "text-anchor": "middle" });
    caption.textContent = label;
    g.append(caption);
  }
  return g;
}

export function buildGuide(guide, x, plot) {
  const g = svgEl("g", { class: "c-guide" });
  g.append(svgEl("line", { x1: x, x2: x, y1: plot.y1, y2: plot.y0 }));
  const text = svgEl("text", { x: x + 4, y: plot.y1 + 10, "text-anchor": "start" });
  text.textContent = guide.label ?? "";
  g.append(text);
  return g;
}
