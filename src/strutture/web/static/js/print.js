// Builds the print-only header of the "relazione di calcolo" (cartiglio + full input echo) and
// prepends it to the results sheet; the rest of the sheet (already built by results.js) is
// reused as-is -- `css/print.css` reshapes colours/chrome for `@media print`.
import { el } from "./dom.js";
import { readJSON, writeJSON } from "./storage.js";
import { humanize } from "./output-schema.js";

const CARTIGLIO_KEY = "sm.cartiglio";

export function cartiglioFields() {
  return readJSON(CARTIGLIO_KEY, { progetto: "", committente: "" });
}

function saveCartiglio(next) {
  writeJSON(CARTIGLIO_KEY, next);
}

function buildCartiglioInput(labelText, key, current, onChange) {
  const wrap = el("label", { class: "print-cartiglio-field" });
  wrap.append(el("span", { text: labelText }));
  const input = el("input", { type: "text", value: current[key] || "" });
  input.addEventListener("input", () => onChange({ ...current, [key]: input.value }));
  wrap.append(input);
  return wrap;
}

function buildCartiglio(tool, mode) {
  const current = cartiglioFields();
  const section = el("section", { class: "print-cartiglio" });
  section.append(buildCartiglioInput("Progetto", "progetto", current, saveCartiglio));
  section.append(buildCartiglioInput("Committente", "committente", current, saveCartiglio));
  const meta = el("dl", { class: "print-cartiglio-meta" });
  const entries = [
    ["Strumento", (tool && tool.title) || ""],
    ["Norma", (tool && tool.norm) || ""],
    ["Data", new Intl.DateTimeFormat("it-IT").format(new Date())],
    ["Modalità", mode || "standard"],
  ];
  for (const [term, value] of entries) {
    meta.append(el("dt", { text: term }));
    meta.append(el("dd", { text: value }));
  }
  section.append(meta);
  return section;
}

// `fields` (forms' Field[]) is optional: when the caller does not supply it, every non-empty
// input is listed, ungrouped, with a humanised label -- still no raw key ever shown bare.
function buildInputEcho(fields, inputsEcho) {
  const section = el("section", { class: "print-inputs" });
  section.append(el("h3", { text: "Dati di input" }));
  const groups = new Map();
  const order = [];
  const entries =
    fields && fields.length > 0
      ? fields.map((field) => [field.group || "", field.name, field.label])
      : Object.keys(inputsEcho || {}).map((name) => ["", name, humanize(name)]);
  for (const [groupName, name, label] of entries) {
    if (!groups.has(groupName)) {
      groups.set(groupName, []);
      order.push(groupName);
    }
    groups.get(groupName).push([name, label]);
  }
  let hasAnyValue = false;
  for (const groupName of order) {
    const dl = el("dl", { class: "print-inputs-list" });
    for (const [name, label] of groups.get(groupName)) {
      const value = inputsEcho ? inputsEcho[name] : undefined;
      if (value === null || value === undefined || value === "") continue;
      dl.append(el("dt", { text: label }));
      dl.append(el("dd", { text: String(value) }));
    }
    if (dl.children.length === 0) continue; // skip empty groups instead of an orphan heading
    hasAnyValue = true;
    if (groupName) section.append(el("h4", { text: groupName }));
    section.append(dl);
  }
  if (!hasAnyValue) section.append(el("p", { text: "Dati di input non disponibili" }));
  return section;
}

// root = the results-pane container that already holds the rendered sheet (verdict, groups,
// tables, charts); this only inserts the print-only cartiglio + input echo at the top of it.
export function buildRelazione(root, { tool, inputsEcho, fields, mode } = {}) {
  const existing = root.querySelector(".print-relazione-head");
  if (existing) existing.remove();
  const head = el("div", { class: "print-relazione-head" });
  head.append(buildCartiglio(tool, mode));
  head.append(buildInputEcho(fields, inputsEcho));
  root.prepend(head);
}
