// Renders a Report into the results sheet + the sticky Sintesi (WORKBENCH_SPEC #4/#8). Listens to
// `strutture:tool-schema`, `strutture:run-start`/`run-result`/`results-stale`, dispatches
// `strutture:results-rendered`. On every run after the first, the SAME group DOM nodes are reused
// (results-groups.js/results-rows.js via results-toolbar.js's `mountGroup`) instead of clearing
// `#results-root` -- so scroll position, open/closed groups and focus survive, and only the value
// cells that actually changed get `data-changed` (results-diff.js).
import { el, clear } from "./dom.js";
import { describeOutput, extractByPredicate, readPath, rowsHighlightPairs, firstChartNode } from "./output-schema.js";
import { describeFields } from "./schema.js";
import { buildMessageList, appendScalarGroup, appendGroupSection } from "./results-groups.js";
import { appendRowsSection } from "./results-rows.js";
import { buildToolbar, createCopyStatus, mountGroup, unmountGroup } from "./results-toolbar.js";
import { buildCheckRow, sortChecks } from "./verdict.js";
import { renderSintesi, renderBottomBar, initSintesiCollapse } from "./sintesi.js";
import { diffScalarPaths, diffChecks, markChanged, captureViewState, restoreViewState, sameValue } from "./results-diff.js";
import { readJSON, writeJSON } from "./storage.js";

const PASSAGGI_ID = "r-group-passaggi";
const LEGACY_ID = "r-group-legacy";
const VERIFICHE_ID = "r-group-verifiche";
const WARNINGS_ID = "r-warnings-panel";
const PASSAGGI_LABEL = "Passaggi di calcolo";
const LEGACY_LABEL = "Solo modalità Excel";
// WORKBENCH_SPEC #3/#9 + finding J seam: muro-sostegno's Verifiche list alone made the sheet
// 1716px tall at first render (target <=900px). Only the failed checks plus the 3 highest
// utilisations render up front; the rest fold behind "Mostra tutte le N verifiche", state
// persisted per tool. (Finding J tightened this from 5 to 3 -- the remaining budget after moving
// the Sintesi sketch beside the verdict (finding B) and collapsing the toolbar to one row
// (finding E) still needed a few more rows folded away to clear 900px on muro-sostegno's 16 checks.)
const CHECKS_FOLD_MIN = 3;

function renderEmpty(root) {
  clear(root);
  root.append(el("p", { class: "r-empty", text: "Compila i dati e premi Calcola. Oppure carica l'esempio." }));
}

function groupStorageKey(toolName) {
  return `sm.ui.resultGroups.${toolName}`;
}

function buildIsOpen(toolName) {
  const persisted = readJSON(groupStorageKey(toolName), {});
  return (id, fallback) => (id in persisted ? persisted[id] : fallback);
}

function persistOpen(toolName, id, open) {
  const persisted = readJSON(groupStorageKey(toolName), {});
  writeJSON(groupStorageKey(toolName), { ...persisted, [id]: open });
}

function makeRegisterGroup(toolName, groups) {
  return (group) => {
    groups.push(group);
    if (group.header.dataset.persistWired) return;
    group.header.dataset.persistWired = "true";
    group.header.addEventListener("click", () => persistOpen(toolName, group.id, group.header.getAttribute("aria-expanded") === "true"));
  };
}

// Finding E: the WARNING COUNT is spoken once, in the Sintesi's own button ("1 avviso" / "2
// avvisi", sintesi.js) -- this is the detail list it opens, so its own summary names the content
// rather than repeating the count a second time.
function buildWarningsPanel(warnings) {
  const details = el("details", { class: "r-warnings-details", id: WARNINGS_ID });
  details.append(el("summary", { text: "Dettaglio avvisi" }));
  details.append(buildMessageList(warnings, "r-warnings"));
  return details;
}

function checksExpandedKey(toolName) {
  return `sm.ui.checksExpanded.${toolName}`;
}

function buildCheckFoldToggle(total, hiddenRows, toolName) {
  const label = (open) => (open ? "Mostra solo le principali" : `Mostra tutte le ${total} verifiche`);
  const expanded = readJSON(checksExpandedKey(toolName), false);
  hiddenRows.forEach((row) => {
    row.hidden = !expanded;
  });
  const button = el("button", {
    type: "button",
    class: "r-action r-check-fold",
    "aria-expanded": String(expanded),
    text: label(expanded),
  });
  button.addEventListener("click", () => {
    const next = button.getAttribute("aria-expanded") !== "true";
    button.setAttribute("aria-expanded", String(next));
    button.textContent = label(next);
    hiddenRows.forEach((row) => {
      row.hidden = !next;
    });
    writeJSON(checksExpandedKey(toolName), next);
  });
  return button;
}

function renderVerifiche(container, checks, changedCheckNames, registerGroup, toolName) {
  if (checks.length === 0) {
    unmountGroup(VERIFICHE_ID);
    return;
  }
  const sorted = sortChecks(checks);
  const failed = sorted.filter((check) => !check.passed).length;
  const group = mountGroup(container, VERIFICHE_ID, `Verifiche (${checks.length})`, { defaultOpen: true, badge: failed });
  group.section.classList.add("r-group--checks");
  clear(group.body);
  group.body.dataset.filter = group.body.dataset.filter || "all";

  const visibleCount = Math.min(sorted.length, Math.max(failed, CHECKS_FOLD_MIN));
  const hiddenRows = [];
  sorted.forEach((check, index) => {
    const row = buildCheckRow(check);
    if (changedCheckNames.has(check.name)) markChanged(row);
    group.body.append(row);
    if (index >= visibleCount) hiddenRows.push(row);
  });
  if (hiddenRows.length > 0) group.body.append(buildCheckFoldToggle(sorted.length, hiddenRows, toolName));

  registerGroup(group);
}

// Exposed per DESIGN_SPEC #5/WORKBENCH_SPEC #8 (`results.js` -> `renderReport(root, {report,
// outputNodes, tool, previous})`). `previous` is the last-rendered Report for the SAME tool, or
// undefined/null on the first render -- callers that want a hard reset just omit it.
export function renderReport(root, { report, outputNodes, tool, previous }) {
  const toolName = tool ? tool.name : "strumento";

  if (!report) {
    root.dataset.tool = toolName;
    renderEmpty(root);
    const sintesiRoot = document.getElementById("sintesi");
    if (sintesiRoot) clear(sintesiRoot);
    return { hasChart: false };
  }

  const freshMount = root.dataset.tool !== toolName || !document.getElementById("r-groups") || !root.contains(document.getElementById("r-groups"));
  const scrollHost = document.getElementById("results-pane") || window;
  const viewState = freshMount ? null : captureViewState(scrollHost);
  root.classList.remove("r-sheet--stale");

  const data = report.data || {};
  const checks = report.checks || [];
  const warnings = report.warnings || [];
  const errors = report.errors || [];
  const legacyMode = Boolean(report.inputs_echo && report.inputs_echo.legacy_compat);

  const legacySplit = extractByPredicate(outputNodes || [], (node) => node.legacyOnly);
  const sketchSplit = extractByPredicate(legacySplit.rest, (node) => node.kind === "sketch");
  const highlightSplit = extractByPredicate(sketchSplit.rest, (node) => node.kind === "scalar" && node.highlight);
  const treeNodes = highlightSplit.rest;
  const scalarHighlights = highlightSplit.matched
    .map((node) => ({ node, value: readPath(data, node.path) }))
    .filter((pair) => pair.value !== null && pair.value !== undefined);
  // A `rows` node stays IN `treeNodes` (its table still renders in full) even when one of its
  // columns is highlighted -- see output-schema.js's rowsHighlightPairs for why that one is
  // additive rather than hoisted-and-removed like a plain scalar highlight.
  const highlightPairs = [...scalarHighlights, ...rowsHighlightPairs(treeNodes, data)].slice(0, 3);
  const sketchPairs = sketchSplit.matched.map((node) => ({ node, value: readPath(data, node.path) }));
  // Orchestrator finding: no checks, no highlights, no sketch -- the Sintesi would otherwise be
  // visibly empty. Only computed in that exact case (an unconditional tree walk on every render
  // would be pure overhead for the common case, which already has plenty to show).
  const chartFallback =
    checks.length === 0 && highlightPairs.length === 0 && sketchPairs.length === 0
      ? (() => {
          const node = firstChartNode(treeNodes);
          const rows = node ? readPath(data, node.path) : undefined;
          return node && Array.isArray(rows) && rows.length > 0 ? { node, rows } : null;
        })()
      : null;

  const hasPrevious = Boolean(previous) && !freshMount;
  const changedPaths = new Set(hasPrevious ? diffScalarPaths(treeNodes, previous.data || {}, data) : []);
  if (hasPrevious) {
    // Plain SCALAR highlights (e.g. `p_h_kNm2`) never appear in `treeNodes` -- describeOutput
    // hoists them out before `diffScalarPaths` above ever walks the tree -- so without this their
    // Sintesi figure would never get `data-changed`, even though it is the single most prominent
    // number on screen (WORKBENCH_SPEC #2 "changed values flash").
    for (const pair of scalarHighlights) {
      if (!sameValue(readPath(previous.data || {}, pair.node.path), pair.value)) changedPaths.add(pair.node.path);
    }
    const previousRowsHighlights = new Map(rowsHighlightPairs(treeNodes, previous.data || {}).map((pair) => [pair.node.path, pair.value]));
    for (const pair of highlightPairs) {
      if (previousRowsHighlights.has(pair.node.path) && previousRowsHighlights.get(pair.node.path) !== pair.value) {
        changedPaths.add(pair.node.path);
      }
    }
  }
  const changedCheckNames = new Set(hasPrevious ? diffChecks(previous.checks || [], checks) : []);

  const sintesiRoot = document.getElementById("sintesi");
  if (sintesiRoot) {
    sintesiRoot.removeAttribute("aria-busy");
    renderSintesi(sintesiRoot, { report, highlightPairs, sketchPairs, chartFallback, previousData: hasPrevious ? previous.data : undefined });
    for (const path of changedPaths) {
      const figureValue = sintesiRoot.querySelector(`.r-si-figure[data-field="${CSS.escape(path)}"] .r-si-figure-value`);
      if (figureValue) markChanged(figureValue);
    }
    if (changedCheckNames.size > 0) {
      const etaValue = sintesiRoot.querySelector(".r-si-eta-value");
      if (etaValue) markChanged(etaValue);
    }
  }
  renderBottomBar(document.getElementById("bottom-bar"), { report, highlightPairs });

  if (freshMount) {
    clear(root);
    root.dataset.tool = toolName;
    root.append(el("div", { id: "r-chrome" }), el("div", { id: "r-groups" }));
  }
  const chrome = document.getElementById("r-chrome");
  const groupsHost = document.getElementById("r-groups");
  clear(chrome);

  const copyCtx = createCopyStatus(root);
  if (errors.length > 0) chrome.append(buildMessageList(errors, "r-errors"));
  if (warnings.length > 0) chrome.append(buildWarningsPanel(warnings));
  chrome.append(el("h2", { id: "results-head", tabindex: "-1", text: (tool && tool.title) || "Risultati" }));
  if (tool && tool.norm) chrome.append(el("p", { class: "r-norm", text: tool.norm }));

  // Finding E: "Stampa relazione" joins the SAME compact toolbar row as "Solo non soddisfatte" /
  // "Espandi tutto" (built below, once `groups` is populated) instead of standing alone as its
  // own tall button above them. Click handling lives in js/relazione-overlay.js (a document-level
  // delegated listener -- this button is rebuilt on every render, so nothing is wired here
  // directly): WORKBENCH_SPEC §11 opens the report personalisation overlay, which builds the
  // printed document FROM THE DATA into its own print-only container, never by reshaping this
  // interactive tree.
  const printBtn = el("button", { type: "button", class: "r-print-trigger", text: "Stampa relazione" });

  const isOpen = buildIsOpen(toolName);
  const groups = [];
  const registerGroup = makeRegisterGroup(toolName, groups);
  // The Sintesi's own chart fallback (sintesi.js) already draws this SAME rows node's chart as a
  // preview -- its own group below still renders (the accessible table stays reachable there),
  // just without a second copy of the chart itself: two live copies of the same `data-series`
  // paths doubled the DOM (measured: a chart-colour test expecting 2 series paths found 4) and,
  // worse, made the sticky #sintesi tall enough to visually cover the toolbar underneath it once
  // scrolled on a narrow viewport.
  const ctx = { copyCtx, changedPaths, registerGroup, isOpen, suppressChartPath: chartFallback ? chartFallback.node.path : undefined };

  renderVerifiche(groupsHost, checks, changedCheckNames, registerGroup, toolName);

  const passaggiNodes = treeNodes.filter((node) => node.kind === "scalar");
  appendScalarGroup(groupsHost, PASSAGGI_ID, PASSAGGI_LABEL, passaggiNodes, data, { ...ctx, isOpen: undefined, defaultOpen: false });

  let hasChart = false;
  for (const node of treeNodes) {
    if (node.kind === "group") {
      if (appendGroupSection(groupsHost, node, data, toolName, ctx)) hasChart = true;
    } else if (node.kind === "rows") {
      if (appendRowsSection(groupsHost, node, data, toolName, ctx)) hasChart = true;
    }
  }

  if (legacyMode && legacySplit.matched.length > 0) {
    const legacyScalars = legacySplit.matched.filter((node) => node.kind === "scalar");
    appendScalarGroup(groupsHost, LEGACY_ID, LEGACY_LABEL, legacyScalars, data, ctx);
  } else {
    unmountGroup(LEGACY_ID);
  }

  const toolbar = buildToolbar({
    groups,
    hasChecks: checks.length > 0,
    printBtn,
    canCompare: Boolean(tool && tool.canCompare),
    onFilterChange: (only) => {
      const body = document.getElementById(`${VERIFICHE_ID}-body`);
      if (body) body.dataset.filter = only ? "failed" : "all";
    },
  });
  chrome.append(toolbar);

  if (viewState) {
    restoreViewState(scrollHost, root, viewState);
    // Deferred second pass as a defensive belt-and-braces measure: `strutture:results-rendered`
    // now carries `reason` and main.js (shell) only calls `focusResults()` for "manual"/"example"
    // -- never "live" (WORKBENCH_SPEC #2/#4 seam, fixed in js/main.js) -- so nothing should scroll
    // the pane back to top on a live re-render anymore. Re-applying the restore one frame later
    // costs nothing when that is already true, and keeps this file correct on its own even if a
    // future caller ever dispatches `results-rendered` without going through main.js's gate.
    requestAnimationFrame(() => restoreViewState(scrollHost, root, viewState));
  }
  if (sintesiRoot) initSintesiCollapse(sintesiRoot);

  return { hasChart };
}

let currentTool = null;
let previousReport = null;

// Read-only snapshot for js/relazione-print.js/relazione-overlay.js (WORKBENCH_SPEC §10/§11): the
// last successfully rendered tool/report, the SAME state this module renders from -- so the
// printed document/overlay is never built from a copy of it that could quietly drift out of sync.
export function getReportState() {
  return { tool: currentTool, report: previousReport };
}

document.addEventListener("strutture:tool-schema", (event) => {
  const { name, output, input, title, norm } = event.detail;
  const fields = describeFields(input || {});
  // WORKBENCH_SPEC §13.3: the "Confronta con Excel" toggle only exists "when the input schema has
  // legacy_compat" -- no per-tool name check, purely schema-driven like every other hint.
  const canCompare = fields.some((field) => field.name === "legacy_compat");
  currentTool = { name, output, title, norm, fields, canCompare, outputNodes: describeOutput(output) };
  previousReport = null;
  const root = document.getElementById("results-root");
  if (root) renderEmpty(root);
  const sintesiRoot = document.getElementById("sintesi");
  if (sintesiRoot) clear(sintesiRoot);
});

document.addEventListener("strutture:run-start", () => {
  const root = document.getElementById("results-root");
  if (root) root.setAttribute("aria-busy", "true");
  const sintesiRoot = document.getElementById("sintesi");
  if (sintesiRoot) sintesiRoot.setAttribute("aria-busy", "true");
});

// `strutture:results-stale` only carries `{name}` in the current forms-live implementation (its
// own comments describe the two Italian messages below but never send which one applies) -- an
// invalid field is already marked `aria-invalid="true"` by the forms package (DESIGN_SPEC #3),
// so that is read directly instead of a `reason` the event does not actually provide.
document.addEventListener("strutture:results-stale", (event) => {
  const { name } = event.detail || {};
  if (!currentTool || currentTool.name !== name) return;
  const root = document.getElementById("results-root");
  if (root) root.classList.add("r-sheet--stale");
  const sintesiRoot = document.getElementById("sintesi");
  if (!sintesiRoot) return;
  let chip = sintesiRoot.querySelector(".r-si-chip");
  if (!chip) {
    chip = el("p", { class: "r-si-chip", role: "status" });
    sintesiRoot.prepend(chip);
  }
  const invalid = Boolean(document.querySelector('#form-root [aria-invalid="true"]'));
  const text = invalid ? "dati non validi — risultati precedenti" : "Dati modificati — premi Calcola";
  if (chip.textContent !== text) chip.textContent = text; // avoid re-announcing an unchanged chip
});

document.addEventListener("strutture:run-result", (event) => {
  const { name, status, report, reason } = event.detail;
  if (!currentTool || currentTool.name !== name) return;
  const root = document.getElementById("results-root");
  if (!root) return;
  root.removeAttribute("aria-busy");
  const { hasChart } = renderReport(root, { report, outputNodes: currentTool.outputNodes, tool: currentTool, previous: previousReport });
  previousReport = report && report.ok !== undefined ? report : previousReport;
  document.dispatchEvent(
    new CustomEvent("strutture:results-rendered", { detail: { name, ok: Boolean(status === 200 && report && report.ok), hasChart, reason } })
  );
});
