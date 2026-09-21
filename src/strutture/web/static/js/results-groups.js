// Scalar row / group section builders for the results tree (results.js). Split out of
// results.js (module-length guideline); depends on results-rows.js for the one `kind: "rows"`
// leaf so the group/scalar recursion and the chart+table leaf stay in separate files.
import { el } from "./dom.js";
import { readPath } from "./output-schema.js";
import { valueNode, formatValue } from "./format.js";
import { symbolNode } from "./symbols.js";
import { appendRowsSection } from "./results-rows.js";

// Clause comes from the field's own `node.clause` when the schema carries one (per-field clause
// hint); the tool-level `norm` is printed once under `#results-head` instead of repeated on every
// row (DESIGN_SPEC review: repeating the same clause on 20+ rows encodes nothing).
export function buildScalarRow(node, value) {
  const row = el("div", { class: "r-row", "data-field": node.name });
  if (node.highlight) row.dataset.highlight = "true";
  row.append(el("span", { class: "r-cell r-cell-symbol" }, node.symbol ? [symbolNode(node.symbol)] : []));
  row.append(el("span", { class: "r-cell r-cell-label", text: node.label }));
  const { title } = formatValue(value, node);
  const valueCell = el("span", { class: "r-cell r-cell-value" }, [valueNode(value, node)]);
  if (title) valueCell.title = title;
  row.append(valueCell);
  row.append(el("span", { class: "r-cell r-cell-unit", text: node.unit !== undefined ? node.unit : "" }));
  if (node.clause) row.append(el("span", { class: "r-cell r-cell-clause", text: node.clause }));
  return row;
}

// No `role="alert"` here even for errors: `#results-pane` (the parent) is already the one
// statically-declared `aria-live="polite"` region (DESIGN_SPEC §3 "nothing else is live"), so
// inserting this list already gets announced without adding a second, redundant live region.
export function buildMessageList(messages, className) {
  const wrap = el("div", { class: className });
  for (const message of messages) wrap.append(el("p", { text: message }));
  return wrap;
}

export function appendScalarGroup(container, title, nodes, data) {
  const rows = [];
  for (const node of nodes) {
    const value = readPath(data, node.path);
    if (value === null || value === undefined) continue;
    rows.push(buildScalarRow(node, value));
  }
  if (rows.length === 0) return;
  const section = el("section", { class: "r-group" });
  if (title) section.append(el("h3", { text: title }));
  for (const row of rows) section.append(row);
  container.append(section);
}

export function appendGroupSection(container, node, data, level, toolName) {
  const section = el("section", { class: "r-group" });
  const heading = `h${Math.min(level, 6)}`;
  section.append(el(heading, { text: node.label }));
  const hasChart = appendChildren(section, node.children, data, level + 1, toolName);
  container.append(section);
  return hasChart;
}

export function appendChildren(container, nodes, data, level, toolName) {
  let hasChart = false;
  for (const node of nodes) {
    if (node.kind === "scalar") {
      const value = readPath(data, node.path);
      if (value === null || value === undefined) continue;
      container.append(buildScalarRow(node, value));
    } else if (node.kind === "group") {
      if (appendGroupSection(container, node, data, level, toolName)) hasChart = true;
    } else if (node.kind === "rows") {
      if (appendRowsSection(container, node, data, toolName)) hasChart = true;
    }
  }
  return hasChart;
}
