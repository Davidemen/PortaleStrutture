// Scalar row + collapsible group builders for the results tree (results.js). Header = title ·
// key-value preview · failed-check badge (WORKBENCH_SPEC #4). Each group's row CONTENT is rebuilt
// on every render (cheap), but the group's own header/body DOM node is reused across renders via
// `mountGroup` (results-toolbar.js) -- so its open/closed state and the scroll position never
// move, and a changed value only marks that one row (`data-changed`), never the whole tree.
import { el, clear } from "./dom.js";
import { readPath, groupPreviewPairs } from "./output-schema.js";
import { valueNode, formatValue, formatCopyValue, formatUnit } from "./format.js";
import { symbolNode } from "./symbols.js";
import { appendRowsSection } from "./results-rows.js";
import { wireValueCopy, mountGroup, unmountGroup, groupId } from "./results-toolbar.js";
import { markChanged } from "./results-diff.js";

export { groupId };

export function buildScalarRow(node, value, ctx = {}) {
  const row = el("div", { class: "r-row", "data-field": node.path });
  if (node.highlight) row.dataset.highlight = "true";
  row.append(el("span", { class: "r-cell r-cell-symbol" }, node.symbol ? [symbolNode(node.symbol)] : []));
  row.append(el("span", { class: "r-cell r-cell-label", text: node.label }));
  const { title } = formatValue(value, node);
  const valueCell = el("span", { class: "r-cell r-cell-value" }, [valueNode(value, node)]);
  if (title) valueCell.title = title;
  row.append(valueCell);
  row.append(el("span", { class: "r-cell r-cell-unit", text: node.unit !== undefined ? formatUnit(node.unit) : "" }));
  if (node.clause) row.append(el("span", { class: "r-cell r-cell-clause", text: node.clause }));
  if (ctx.copyCtx) wireValueCopy(valueCell, formatCopyValue(value), ctx.copyCtx.announce);
  if (ctx.changedPaths && ctx.changedPaths.has(node.path)) markChanged(valueCell);
  return row;
}

export function buildMessageList(messages, className) {
  const wrap = el("div", { class: className });
  for (const message of messages) wrap.append(el("p", { text: message }));
  return wrap;
}

export function appendScalarGroup(container, id, title, nodes, data, ctx = {}) {
  const rows = [];
  for (const node of nodes) {
    const value = readPath(data, node.path);
    if (value === null || value === undefined) continue;
    rows.push(buildScalarRow(node, value, ctx));
  }
  if (rows.length === 0) {
    // A print build never has a previous mount of its OWN to remove -- and, being a fresh id-less
    // container, must never risk `unmountGroup`'s `document.getElementById(id)` adopting (and
    // deleting) the SAME group still live in the interactive tree on screen.
    if (!ctx.print) unmountGroup(id);
    return null;
  }
  const defaultOpen = ctx.isOpen ? ctx.isOpen(id, Boolean(ctx.defaultOpen)) : Boolean(ctx.defaultOpen);
  const group = mountGroup(container, id, title, { defaultOpen, print: ctx.print });
  clear(group.body);
  for (const row of rows) group.body.append(row);
  if (ctx.registerGroup) ctx.registerGroup(group);
  return group;
}

export function appendGroupSection(container, node, data, toolName, ctx = {}) {
  const id = groupId(node.path);
  const previewPairs = groupPreviewPairs(node, data, 2);
  const scratch = el("div"); // children are built off-DOM so an all-empty group can be detected
  const hasChart = appendChildren(scratch, node.children, data, toolName, ctx);
  if (scratch.childElementCount === 0) {
    if (!ctx.print) unmountGroup(id);
    return false;
  }
  const defaultOpen = ctx.isOpen ? ctx.isOpen(id, false) : false;
  const group = mountGroup(container, id, node.label, { defaultOpen, previewPairs, print: ctx.print });
  clear(group.body);
  group.body.append(...scratch.children);
  if (ctx.registerGroup) ctx.registerGroup(group);
  return hasChart;
}

export function appendChildren(container, nodes, data, toolName, ctx = {}) {
  let hasChart = false;
  for (const node of nodes) {
    if (node.kind === "scalar") {
      const value = readPath(data, node.path);
      if (value === null || value === undefined) continue;
      container.append(buildScalarRow(node, value, ctx));
    } else if (node.kind === "group") {
      if (appendGroupSection(container, node, data, toolName, ctx)) hasChart = true;
    } else if (node.kind === "rows") {
      if (appendRowsSection(container, node, data, toolName, ctx)) hasChart = true;
    }
  }
  return hasChart;
}
