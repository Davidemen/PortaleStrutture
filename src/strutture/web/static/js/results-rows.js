// Row-tuple output section: builds the {chart?, table} pair for one `kind: "rows"` output node.
// Split out of results.js (module-length guideline) since chart-args mapping + the figure/table
// wiring is a self-contained seam that doesn't need the scalar/group builders.
import { el, clear } from "./dom.js";
import { readPath } from "./output-schema.js";
import { renderRows } from "./table.js";
import { buildPrintTable } from "./relazione-table.js";
import { renderChart } from "./chart.js";
import { mountGroup, unmountGroup, groupId } from "./results-toolbar.js";

// Exported for the Sintesi's own empty-block chart fallback (sintesi.js, design review
// 2026-09-21) -- the SAME mapping from a `rows` node's `chart` hint to `renderChart`'s args, not
// a second implementation of it.
export function buildChartArgs(node, rows) {
  const chart = node.chart;
  const series = (chart.y || []).map((key, index) => {
    const column = node.columns.find((c) => c.name === key) || {};
    return { key, label: column.label || key, symbol: column.symbol || null, className: `c-series-${index + 1}` };
  });
  return { rows, chart, series, labels: { xLabel: chart.x_label, yLabel: chart.y_label }, guides: chart.guides };
}

// Returns true when a chart was actually drawn (fed back up as the `hasChart` result). The SVG
// stays aria-hidden (chart.js) with the table as the accessible alternative -- hence <figure>.
// The whole rows section is itself a collapsible group (WORKBENCH_SPEC #4: "Result groups are
// collapsible... Row tables and charts as today, inside their collapsible group"), reused across
// live re-renders via `mountGroup` -- only the table body content is rebuilt each run.
export function appendRowsSection(
  container,
  node,
  data,
  toolName,
  { registerGroup, isOpen, print, chart = true, tabellePolicy, suppressChartPath } = {},
) {
  const rows = readPath(data, node.path) || [];
  const id = groupId(node.path);
  if (rows.length === 0) {
    if (!print) unmountGroup(id); // see results-groups.js for why this is skipped in print mode
    return false;
  }
  const defaultOpen = isOpen ? isOpen(id, false) : false;
  const group = mountGroup(container, id, node.label, { defaultOpen, print });
  clear(group.body);
  let hasChart = false;
  const showChart = chart && node.path !== suppressChartPath;
  if (node.chart && showChart) {
    const figure = el("figure", { class: "r-chart" });
    group.body.append(figure);
    hasChart = Boolean(renderChart(figure, buildChartArgs(node, rows)));
    if (hasChart) {
      // Describe the axes, not the group title again: the group header and the table `<caption>`
      // right below already say `node.label` (print especially printed it 3x in a row).
      const axes = node.chart.y_label && node.chart.x_label ? `${node.chart.y_label} in funzione di ${node.chart.x_label}` : node.label;
      figure.append(el("figcaption", { text: axes }));
    } else {
      figure.remove();
    }
  }
  const tableHost = el("div");
  group.body.append(tableHost);
  // Print (WORKBENCH_SPEC §10): unpaged, no copy/CSV actions -- `buildPrintTable` reuses table.js's
  // OWN row/header builder (`buildTable`) rather than a second formatting implementation, only the
  // paging/actions/truncation-past-2000-rows policy differs.
  if (print) tableHost.append(buildPrintTable({ ...node, toolName }, rows, tabellePolicy));
  else renderRows(tableHost, { ...node, toolName }, rows);
  if (registerGroup) registerGroup(group);
  return hasChart;
}
