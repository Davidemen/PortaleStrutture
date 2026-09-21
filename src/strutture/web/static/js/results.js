// Renders a Report into the results sheet: verdict, marker rows (<=3 highlighted outputs,
// hoisted to the top), then the rest of the tree as titled groups / tables / charts. Listens to
// `strutture:tool-schema` and `strutture:run-start`/`run-result`, dispatches
// `strutture:results-rendered`. Scalar/group builders live in results-groups.js, the
// chart+table row section in results-rows.js (module-length guideline).
import { el, clear } from "./dom.js";
import { describeOutput, extractByPredicate, readPath } from "./output-schema.js";
import { renderVerdict } from "./verdict.js";
import { buildRelazione } from "./print.js";
import { describeFields } from "./schema.js";
import { buildScalarRow, buildMessageList, appendScalarGroup, appendGroupSection } from "./results-groups.js";
import { appendRowsSection } from "./results-rows.js";

const PASSAGGI_LABEL = "Passaggi di calcolo";
const LEGACY_LABEL = "Solo modalità Excel";

function renderEmpty(root) {
  clear(root);
  root.append(el("p", { class: "r-empty", text: "Compila i dati e premi Calcola. Oppure carica l'esempio." }));
}

export function renderReport(root, { report, outputNodes, tool }) {
  clear(root);
  if (!report) {
    renderEmpty(root);
    return { hasChart: false };
  }

  const errors = report.errors || [];
  const warnings = report.warnings || [];
  if (errors.length > 0) root.append(buildMessageList(errors, "r-errors"));
  if (warnings.length > 0) root.append(buildMessageList(warnings, "r-warnings"));

  root.append(el("h2", { id: "results-head", tabindex: "-1", text: (tool && tool.title) || "Risultati" }));
  // The tool's `norm` is printed once here instead of on every row (see buildScalarRow above).
  if (tool && tool.norm) root.append(el("p", { class: "r-norm", text: tool.norm }));

  const toolName = tool ? tool.name : "strumento";
  const legacyMode = Boolean(report.inputs_echo && report.inputs_echo.legacy_compat);
  const printBtn = el("button", { type: "button", class: "r-print-trigger" , text: "Stampa relazione"});
  printBtn.addEventListener("click", () => {
    buildRelazione(root, {
      tool,
      inputsEcho: report.inputs_echo,
      fields: tool ? tool.fields : undefined,
      mode: legacyMode ? "foglio Excel" : "standard",
    });
    window.print();
  });
  root.append(printBtn);
  const legacySplit = extractByPredicate(outputNodes || [], (node) => node.legacyOnly);
  const baseNodes = legacySplit.rest;
  const legacyNodes = legacyMode ? legacySplit.matched : [];

  const data = report.data || {};
  const highlightSplit = extractByPredicate(baseNodes, (node) => node.kind === "scalar" && node.highlight);
  const highlightPairs = highlightSplit.matched
    .slice(0, 3)
    .map((node) => ({ node, value: readPath(data, node.path) }))
    .filter((pair) => pair.value !== null && pair.value !== undefined);

  const verdictRoot = el("div", { class: "r-verdict" });
  root.append(verdictRoot);
  renderVerdict(verdictRoot, { checks: report.checks || [], highlights: highlightPairs, ok: report.ok });

  if (highlightPairs.length > 0) {
    const marker = el("section", { class: "r-group r-group--marker" });
    for (const { node, value } of highlightPairs) marker.append(buildScalarRow(node, value));
    root.append(marker);
  }

  const topScalars = highlightSplit.rest.filter((node) => node.kind === "scalar");
  const topOther = highlightSplit.rest.filter((node) => node.kind !== "scalar");
  appendScalarGroup(root, PASSAGGI_LABEL, topScalars, data);

  let hasChart = false;
  for (const node of topOther) {
    if (node.kind === "group") {
      if (appendGroupSection(root, node, data, 3, toolName)) hasChart = true;
    } else if (node.kind === "rows") {
      if (appendRowsSection(root, node, data, toolName)) hasChart = true;
    }
  }

  if (legacyMode && legacyNodes.length > 0) {
    const legacyScalars = legacyNodes.filter((node) => node.kind === "scalar");
    appendScalarGroup(root, LEGACY_LABEL, legacyScalars, data);
  }

  return { hasChart };
}

let currentTool = null;

document.addEventListener("strutture:tool-schema", (event) => {
  const { name, output, input, title, norm } = event.detail;
  // Cache the input Field[] (same describeFields the forms package builds) so "Stampa relazione"
  // can print the real input echo with schema labels/groups instead of falling back to raw keys.
  const fields = describeFields(input || {});
  currentTool = { name, output, title, norm, fields };
  const root = document.getElementById("results-root");
  if (root) renderEmpty(root);
});

document.addEventListener("strutture:run-start", () => {
  const root = document.getElementById("results-root");
  if (root) root.setAttribute("aria-busy", "true");
});

document.addEventListener("strutture:run-result", (event) => {
  const { name, status, report } = event.detail;
  if (!currentTool || currentTool.name !== name) return;
  const root = document.getElementById("results-root");
  if (!root) return;
  root.removeAttribute("aria-busy");
  const outputNodes = describeOutput(currentTool.output);
  const { hasChart } = renderReport(root, { report, outputNodes, tool: currentTool });
  document.dispatchEvent(
    new CustomEvent("strutture:results-rendered", { detail: { name, ok: Boolean(status === 200 && report && report.ok), hasChart } })
  );
});
