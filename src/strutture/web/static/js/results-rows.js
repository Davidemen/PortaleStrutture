// Row-tuple output section: builds the {chart?, table} pair for one `kind: "rows"` output node.
// Split out of results.js (module-length guideline) since chart-args mapping + the figure/table
// wiring is a self-contained seam that doesn't need the scalar/group builders.
import { el } from "./dom.js";
import { readPath } from "./output-schema.js";
import { renderRows } from "./table.js";
import { renderChart } from "./chart.js";

function buildChartArgs(node, rows) {
  const chart = node.chart;
  const series = (chart.y || []).map((key, index) => {
    const column = node.columns.find((c) => c.name === key) || {};
    return { key, label: column.label || key, symbol: column.symbol || null, className: `c-series-${index + 1}` };
  });
  return { rows, chart, series, labels: { xLabel: chart.x_label, yLabel: chart.y_label }, guides: chart.guides };
}

// Returns true when a chart was actually drawn (fed back up as the `hasChart` result). The SVG
// stays aria-hidden (chart.js) with the table as the accessible alternative -- hence <figure>.
export function appendRowsSection(container, node, data, toolName) {
  const rows = readPath(data, node.path) || [];
  if (rows.length === 0) return false;
  const section = el("section", { class: "r-group" });
  section.append(el("h3", { text: node.label }));
  let hasChart = false;
  if (node.chart) {
    const figure = el("figure", { class: "r-chart" });
    section.append(figure);
    hasChart = Boolean(renderChart(figure, buildChartArgs(node, rows)));
    if (hasChart) {
      // Describe the axes, not the group title again: the group `<h3>` and the table `<caption>`
      // right below already say `node.label` (print especially printed it 3x in a row).
      const axes = node.chart.y_label && node.chart.x_label ? `${node.chart.y_label} in funzione di ${node.chart.x_label}` : node.label;
      figure.append(el("figcaption", { text: axes }));
    } else {
      figure.remove();
    }
  }
  const tableHost = el("div");
  section.append(tableHost);
  renderRows(tableHost, { ...node, toolName }, rows);
  container.append(section);
  return hasChart;
}
