// The verdict block: pass/fail word (or, for load tools with no checks, a one-line "sintesi"
// built from the highlighted outputs) + one row per Check, each with an optional utilisation bar.
import { el, clear } from "./dom.js";
import { formatValue } from "./format.js";

function checkMark(ok) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 16 16");
  svg.setAttribute("width", "16");
  svg.setAttribute("height", "16");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("class", "r-icon");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", ok ? "M3 8.5 L6.5 12 L13 4" : "M4 4 L12 12 M12 4 L4 12");
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", "currentColor");
  path.setAttribute("stroke-width", "2");
  path.setAttribute("stroke-linecap", "round");
  svg.append(path);
  return svg;
}

// Ratio from check.value/check.limit when present, else parsed from `detail`.
export function utilisation(check) {
  if (typeof check.value === "number" && typeof check.limit === "number" && check.limit !== 0) {
    return check.value / check.limit;
  }
  const detail = check.detail || "";
  const match = detail.match(/(-?\d+(?:[.,]\d+)?)\s*(?:≤|<=|\/)\s*(-?\d+(?:[.,]\d+)?)/);
  if (!match) return null;
  const toNumber = (text) => Number(text.replace(",", "."));
  const limit = toNumber(match[2]);
  if (!limit) return null;
  return toNumber(match[1]) / limit;
}

// `ratio` here is always demand/capacity (<=1 = safe): some tools report the inverse (e.g.
// `OR=4.061` where higher = safer, so `ratio>1` from `utilisation()` is the passing case) --
// `buildBar` reciprocates those before plotting so colour always agrees with `check.passed`.
function buildBar(ratio, passed) {
  const plotted = passed && ratio > 1 ? 1 / ratio : ratio;
  const label = formatValue(plotted, { integer: false }).text;
  const wrap = el("div", { class: "r-bar", role: "img", "aria-label": `sfruttamento ${label}` });
  const track = el("div", { class: "r-bar-track" });
  const fill = el("div", { class: `r-bar-fill ${passed ? "" : "r-bar-fill--over"}` });
  fill.style.setProperty("--util", String(Math.min(Math.max(plotted, 0), 2) / 2));
  track.append(fill);
  wrap.append(track);
  return wrap;
}

function buildCheckRow(check) {
  const row = el("div", { class: `r-check ${check.passed ? "r-check--pass" : "r-check--fail"}` });
  row.append(el("span", { class: "r-check-icon" }, [checkMark(check.passed)]));
  row.append(el("span", { class: "r-check-name", text: check.name }));
  row.append(el("span", { class: "r-check-clause", text: check.clause || "" }));
  row.append(el("span", { class: "r-check-detail", text: check.detail || "" }));
  const ratio = utilisation(check);
  row.append(ratio === null ? el("span", { class: "r-check-nobar" }) : buildBar(ratio, check.passed));
  return row;
}

export function renderVerdict(root, { checks = [], highlights = [], ok = true } = {}) {
  clear(root);
  const head = el("div", { class: "r-verdict-head" });
  if (checks.length > 0) {
    const failing = checks.filter((check) => !check.passed).length;
    head.append(checkMark(ok));
    head.append(
      el("span", {
        class: `r-verdict-word ${ok ? "r-verdict-word--ok" : "r-verdict-word--ko"}`,
        text: ok ? "Tutte le verifiche soddisfatte" : `${failing} verifiche non soddisfatte`,
      })
    );
  } else {
    // Load tools (no checks): the governing values are the marker-yellow rows below (DESIGN_SPEC
    // §0), so this line never restates them -- it only keeps the verdict slot from being empty.
    const text = highlights.length > 0 ? "Risultato evidenziato qui sotto." : "Calcolo completato.";
    head.append(el("span", { class: "r-verdict-sintesi", text }));
  }
  root.append(head);

  if (checks.length > 0) {
    const list = el("div", { class: "r-checks" });
    for (const check of checks) list.append(buildCheckRow(check));
    root.append(list);
  }
}
