// Dati column accordion -- WORKBENCH_SPEC §3. Each section is a `<button aria-expanded
// aria-controls>` disclosure with a one-line collapsed-state summary of its own field values and
// an error-count badge; open/closed state persists per tool. Uses a `sm.ui.openGroups.<tool>` key
// (not the bare `sm.ui.openGroups` DESIGN_SPEC §3 gives the shell's tool-index groups) so the two
// unrelated "open group" concerns never clobber each other in localStorage.
import { el } from "./dom.js";
import { buildField } from "./fields.js";
import { symbolNode } from "./symbols.js";
import { readJSON, writeJSON } from "./storage.js";
import { formatUnit } from "./format.js";

const MAX_SUMMARY_VALUES = 3;
let sectionIdCounter = 0;

function openGroupsKey(tool) {
  return `sm.ui.openGroups.${tool}`;
}

function loadOpenState(tool, names) {
  const saved = readJSON(openGroupsKey(tool), null);
  if (saved && typeof saved === "object") return saved;
  // Default: only the first section open (WORKBENCH_SPEC §3).
  return Object.fromEntries(names.map((name, index) => [name, index === 0]));
}

function saveOpenState(tool, state) {
  writeJSON(openGroupsKey(tool), state);
}

function formatSummaryNumber(value) {
  const rounded = Math.round(value * 100) / 100;
  return String(rounded).replace(".", ",");
}

// `{field, text}`, never a pre-joined string: the DOM renderer below needs `field.symbol` to
// build a real subscript (finding I), which a flattened string could no longer carry.
function summaryToken(field, value) {
  if (value === null || value === undefined || value === "") return null;
  let text = null;
  // Review finding 22 ("symbol tokens only"): a field WITHOUT a symbol contributes its value alone
  // ("rettangolare", "C25/30", "3 righe") -- its label is a whole sentence, and gluing the value to
  // it printed "Forma della sezione trasversalerettangolare". A bare "sì"/"no" says nothing: skipped.
  if (typeof value === "boolean") text = field.symbol ? (value ? "sì" : "no") : null;
  else if (typeof value === "number") text = Number.isFinite(value) ? formatSummaryNumber(value) : null;
  else if (Array.isArray(value)) text = field.kind === "list" ? `${value.length} valori` : `${value.length} righe`;
  else text = String(value);
  if (!text) return null;
  return { field, text: field.unit ? `${text} ${formatUnit(field.unit)}` : text };
}

// "A_X 4 m · B_Y 4 m …" -- symbols where available (real subscripts, finding I), max 3 values.
// Exported (alongside `countErrors` below) purely for the `_harness` node --test unit tests --
// `buildSections` is the only entry point the rest of the app uses.
export function summarizeValues(fields, values) {
  return fields.map((field) => summaryToken(field, values[field.name])).filter(Boolean);
}

function buildTokenNode({ field, text }) {
  const span = el("span", { class: "f-section-summary-token" });
  if (field.symbol) span.append(symbolNode(field.symbol));
  // No leading space here -- `.f-section-summary-token`'s own flex `gap` (forms.css) already
  // spaces the symbol/label from the value; a literal space too would double it up.
  span.append(document.createTextNode(text));
  return span;
}

function paintTokens(summarySpan, tokens, truncated) {
  summarySpan.replaceChildren();
  tokens.forEach((token, index) => {
    if (index > 0) summarySpan.append(document.createTextNode(" · "));
    summarySpan.append(buildTokenNode(token));
  });
  if (truncated) summarySpan.append(document.createTextNode(" …"));
}

// Finding I: "when the summary does not fit, drop whole items and end with '…' (no mid-value
// cut)" -- CSS `text-overflow: ellipsis` truncates by PIXEL, which can slice a value mid-digit;
// this drops whole TOKENS instead, first to the 3-value cap, then (if still too wide for the
// actual rendered column) one more at a time. Skipped while the row has no real layout yet (a
// hidden pane, `clientWidth === 0`) so it never collapses to a single token just because it was
// momentarily off-screen.
function renderSummaryTokens(summarySpan, allTokens) {
  const capped = allTokens.slice(0, MAX_SUMMARY_VALUES);
  if (capped.length === 0) {
    summarySpan.replaceChildren();
    return;
  }
  let visible = capped.length;
  paintTokens(summarySpan, capped, allTokens.length > capped.length);
  if (summarySpan.clientWidth === 0) return;
  while (visible > 1 && summarySpan.scrollWidth > summarySpan.clientWidth + 1) {
    visible -= 1;
    paintTokens(summarySpan, capped.slice(0, visible), true);
  }
}

export function countErrors(fields, errorsByField) {
  return fields.reduce((count, field) => (errorsByField[field.name] ? count + 1 : count), 0);
}

function buildOne(name, sectionFields, open) {
  const bodyId = `f-section-body-${sectionIdCounter++}`;
  const summarySpan = el("span", { class: "f-section-summary", "aria-hidden": "true" });
  const badge = el("span", { class: "f-section-badge", hidden: true, "aria-hidden": "true" });
  const toggle = el(
    "button",
    { type: "button", class: "f-section-toggle", "aria-expanded": String(open), "aria-controls": bodyId },
    [el("span", { class: "f-section-title", text: name || "Dati" }), summarySpan, badge],
  );
  const body = el("div", { class: "f-section-body", id: bodyId });
  body.hidden = !open;
  sectionFields.forEach((field) => body.append(buildField(field)));
  const section = el("section", { class: "f-section", "data-section": name || "" }, [el("h3", {}, [toggle]), body]);
  return {
    name,
    fields: sectionFields,
    section,
    body,
    toggle,
    setSummary: (tokens) => {
      renderSummaryTokens(summarySpan, tokens);
    },
    setBadge: (count) => {
      badge.textContent = count > 0 ? `${count} errori` : "";
      badge.hidden = count === 0;
    },
  };
}

// `sections` = the `Map` groupFields (forms-sections.js) returns. Builds every accordion section,
// wires persistence on toggle, and returns the handles renderForm (forms.js) drives on every
// value/error change plus the "Espandi tutto / Comprimi tutto" pair.
export function buildSections(sections, tool) {
  const names = [...sections.keys()];
  const openState = loadOpenState(tool, names);
  const entries = names.map((name) => buildOne(name, sections.get(name), Boolean(openState[name])));

  const setOpen = (entry, open) => {
    entry.toggle.setAttribute("aria-expanded", String(open));
    entry.body.hidden = !open;
  };
  const persist = () => saveOpenState(tool, Object.fromEntries(entries.map((entry) => [entry.name, entry.toggle.getAttribute("aria-expanded") === "true"])));

  entries.forEach((entry) => {
    entry.toggle.addEventListener("click", () => {
      setOpen(entry, entry.toggle.getAttribute("aria-expanded") !== "true");
      persist();
    });
  });

  return {
    elements: entries.map((entry) => entry.section),
    refresh(values, errorsByField = {}) {
      entries.forEach((entry) => {
        entry.setSummary(summarizeValues(entry.fields, values));
        entry.setBadge(countErrors(entry.fields, errorsByField));
      });
    },
    expandAll() {
      entries.forEach((entry) => setOpen(entry, true));
      persist();
    },
    collapseAll() {
      entries.forEach((entry) => setOpen(entry, false));
      persist();
    },
  };
}
