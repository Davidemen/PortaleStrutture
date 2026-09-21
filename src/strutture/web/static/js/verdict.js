// Check-row primitives shared by the Sintesi (js/sintesi.js, one bar for the governing check) and
// the "Verifiche" results group (js/results-groups.js, the full sorted list). Owns: the pass/fail
// icon, utilisation maths, the bar widget and the sort/governance rules -- no DOM mounting of a
// full list here anymore (that moved into the collapsible group, WORKBENCH_SPEC #4).
import { el } from "./dom.js";
import { formatUtilisation, formatDetail } from "./format.js";

// Review finding 8: some tools still name a check with a raw load-combination key ("Ribaltamento
// STR_1", "Scorrimento SISMA_2 (−kv)") -- the backend is moving these to plain Italian text
// combination by combination, but until every tool is migrated this fallback keeps the literal
// underscore out of what the engineer reads. Only the separator is touched (a space reads as a
// combination label the same way "STR 1"/"SISMA 2" already does elsewhere) -- the rest of the
// string is already correctly capitalised by the backend, so it is never re-cased here.
export function displayCheckName(name) {
  return typeof name === "string" ? name.replace(/_/g, " ") : name;
}

export function checkMark(ok) {
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

// Some tools report the inverse (e.g. `OR=4.061` where higher = safer): normalise those to the
// usual demand/capacity reading (<=1 safe, >1 fails) so sorting, "eta max" and the bar fill all
// agree with `check.passed`, whichever way the raw ratio pointed.
export function effectiveUtilisation(check) {
  const ratio = utilisation(check);
  if (ratio === null) return null;
  return check.passed && ratio > 1 ? 1 / ratio : ratio;
}

// Failed checks first; within each group, highest utilisation (closest to -- or past -- the
// limit) first. Checks with no parseable ratio sort last, in their original order.
export function sortChecks(checks) {
  return checks
    .map((check, index) => ({ check, index, ratio: effectiveUtilisation(check) }))
    .sort((a, b) => {
      if (a.check.passed !== b.check.passed) return a.check.passed ? 1 : -1;
      if (a.ratio === null && b.ratio === null) return a.index - b.index;
      if (a.ratio === null) return 1;
      if (b.ratio === null) return -1;
      return b.ratio - a.ratio;
    })
    .map((entry) => entry.check);
}

// The check to feature in the Sintesi's "eta max" line: the first one after `sortChecks` --
// a failed check outranks every passed one, otherwise the highest utilisation wins.
export function governingCheck(checks) {
  if (!checks || checks.length === 0) return null;
  return sortChecks(checks)[0];
}

export function buildBar(ratio, passed) {
  const plotted = passed && ratio > 1 ? 1 / ratio : ratio;
  const label = formatUtilisation(plotted);
  const wrap = el("div", { class: "r-bar", role: "img", "aria-label": `sfruttamento ${label}` });
  const track = el("div", { class: "r-bar-track" });
  const fill = el("div", { class: `r-bar-fill ${passed ? "" : "r-bar-fill--over"}` });
  fill.style.setProperty("--util", String(Math.min(Math.max(plotted, 0), 2) / 2));
  track.append(fill);
  wrap.append(track);
  return wrap;
}

export function buildCheckRow(check) {
  const row = el("div", { class: `r-check ${check.passed ? "r-check--pass" : "r-check--fail"}`, "data-passed": String(check.passed) });
  row.append(el("span", { class: "r-check-icon" }, [checkMark(check.passed)]));
  const displayName = displayCheckName(check.name);
  row.append(el("span", { class: "r-check-name", text: displayName, title: displayName }));
  row.append(el("span", { class: "r-check-clause", text: check.clause || "" }));
  const detail = formatDetail(check.detail);
  row.append(el("span", { class: "r-check-detail", text: detail, title: detail }));
  const ratio = utilisation(check);
  row.append(ratio === null ? el("span", { class: "r-check-nobar" }) : buildBar(ratio, check.passed));
  return row;
}
