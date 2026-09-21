// "Dati di ingresso" print section (WORKBENCH_SPEC §10): one table per input section -- simbolo |
// descrizione | valore | unità -- for every field the tool has, typed values and defaults
// actually used and advanced options and the calculation mode all included (nothing is folded
// behind "Avanzate" in print). Table-kind fields (soil layers, load cases, plates) are listed row
// by row, with their OWN column units, in a nested table right under their section's main one.
import { el } from "./dom.js";
import { formatValue, formatUnit } from "./format.js";
import { symbolNode } from "./symbols.js";
import { formatListText } from "./list-input.js";

function scalarValueText(field, raw) {
  const value = raw === undefined ? field.default : raw;
  if (value === null || value === undefined) return "—";
  if (field.kind === "boolean") return value ? "sì" : "no";
  // "5; 10; 15,5" -- the Unità column (buildFieldRow) prints "min" once alongside it, together
  // reading as "5; 10; 15,5 min" (design review 2026-09-21, list-input.js).
  if (field.kind === "list") return Array.isArray(value) ? formatListText(value, field.itemKind) : String(value);
  return formatValue(value, field).text;
}

function buildFieldRow(field, inputsEcho) {
  const raw = inputsEcho ? inputsEcho[field.name] : undefined;
  const row = el("tr");
  row.append(el("td", { class: "r-cell-symbol" }, field.symbol ? [symbolNode(field.symbol)] : []));
  row.append(el("td", { text: field.label }));
  row.append(el("td", { class: "r-num", text: scalarValueText(field, raw) }));
  row.append(el("td", { text: formatUnit(field.unit) }));
  return row;
}

function buildTableRows(field, rows) {
  const wrap = el("div", { class: "r-table-print" });
  const table = el("table", { class: "r-table" });
  table.append(el("caption", { text: field.label }));
  const headRow = el("tr");
  for (const column of field.columns || []) {
    headRow.append(el("th", { scope: "col", text: column.unit ? `${column.label} [${formatUnit(column.unit)}]` : column.label }));
  }
  table.append(el("thead", {}, [headRow]));
  const tbody = el("tbody");
  for (const dataRow of rows) {
    const tr = el("tr");
    for (const column of field.columns || []) tr.append(el("td", { class: "r-num", text: formatValue(dataRow[column.name], column).text }));
    tbody.append(tr);
  }
  table.append(tbody);
  wrap.append(table);
  return wrap;
}

function buildSectionTable(groupName, fields, inputsEcho) {
  const section = el("section", { class: "r-group r-group--print" });
  section.append(el("h3", { class: "r-group-title", text: groupName }));
  const body = el("div", { class: "r-group-body" });
  const scalarFields = fields.filter((f) => f.kind !== "table");
  if (scalarFields.length > 0) {
    const table = el("table", { class: "r-table r-inputs-table" });
    const headRow = el("tr", {}, [
      el("th", { scope: "col", text: "Simbolo" }),
      el("th", { scope: "col", text: "Descrizione" }),
      el("th", { scope: "col", text: "Valore" }),
      el("th", { scope: "col", text: "Unità" }),
    ]);
    table.append(el("thead", {}, [headRow]));
    const tbody = el("tbody");
    for (const field of scalarFields) tbody.append(buildFieldRow(field, inputsEcho));
    table.append(tbody);
    body.append(table);
  }
  for (const field of fields.filter((f) => f.kind === "table")) {
    const rows = (inputsEcho && inputsEcho[field.name]) || [];
    body.append(buildTableRows(field, rows));
  }
  section.append(body);
  return section;
}

// Groups fields the SAME way the Dati column does (the `group` hint, order = first appearance;
// ungrouped fields fall into one plain "Dati" section) and builds one table per group.
export function buildInputsSection(fields, inputsEcho) {
  const container = el("div", { class: "print-inputs" });
  container.append(el("h2", { text: "Dati di ingresso" }));
  const order = [];
  const byGroup = new Map();
  for (const field of fields || []) {
    const name = field.group || "Dati";
    if (!byGroup.has(name)) {
      byGroup.set(name, []);
      order.push(name);
    }
    byGroup.get(name).push(field);
  }
  for (const name of order) container.append(buildSectionTable(name, byGroup.get(name), inputsEcho));
  return container;
}
