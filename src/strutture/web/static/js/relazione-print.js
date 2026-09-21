// The browser's OWN print command (File>Print, a right-click "Print"…, any Ctrl/Cmd+P the overlay
// somehow never intercepted) to WORKBENCH_SPEC §10: a printed document is always built FROM THE
// DATA into a dedicated print-only container, the interactive UI is hidden in print
// (css/print.css), and stale results are never exported. WORKBENCH_SPEC §11: every ENTRY POINT
// ("Stampa relazione", the "⋯" menu, Ctrl/Cmd+P) now opens `js/relazione-overlay.js`'s overlay
// instead of printing straight from here -- this module keeps the stale-check/recalculate/refuse
// primitives (reused by the overlay's own "opening applies the stale rule" step) and the
// `beforeprint` FALLBACK for a print the overlay never got a chance to intercept.
import { el, clear } from "./dom.js";
import { runTool } from "./api.js";
import { getReportState } from "./results.js";
import { validateValues } from "./validate.js";
import { visibleValues } from "./forms-sections.js";
import { buildRelazione, resolveOptions } from "./relazione.js";

export const REFUSAL_TEXT = "I risultati non corrispondono ai dati correnti — correggi i dati o ricalcola prima di stampare";
const PRINT_ROOT_ID = "relazione-print-root";

export function ensurePrintRoot() {
  let root = document.getElementById(PRINT_ROOT_ID);
  if (!root) {
    root = el("div", { id: PRINT_ROOT_ID });
    root.hidden = true;
    document.body.append(root);
  }
  return root;
}

function currentForm() {
  return document.querySelector("#form-root form");
}

export function currentValuesAndValidity(fields) {
  const form = currentForm();
  if (!form || !fields) return { values: null, invalid: true };
  const values = visibleValues(form, fields);
  return { values, invalid: Object.keys(validateValues(fields, values)).length > 0 };
}

export function isStaleOnScreen() {
  const root = document.getElementById("results-root");
  return Boolean(root && root.classList.contains("r-sheet--stale"));
}

export function showRefusal() {
  const box = document.getElementById("run-error");
  if (!box) return;
  box.textContent = REFUSAL_TEXT;
  box.hidden = false;
}

export function clearRefusal() {
  const box = document.getElementById("run-error");
  if (box && box.textContent === REFUSAL_TEXT) box.hidden = true;
}

// Recalculates through the SAME run pipeline as a live update (reason "live": never steals focus/
// scroll, WORKBENCH_SPEC §2 seam in main.js) so the on-screen sheet also catches up -- the fresh
// report is used for print/preview either way.
async function recalculate(name, values) {
  document.dispatchEvent(new CustomEvent("strutture:run-start", { detail: { name, reason: "live" } }));
  const { status, report } = await runTool(name, values);
  document.dispatchEvent(new CustomEvent("strutture:run-result", { detail: { name, status, values, report, reason: "live" } }));
  return report && report.ok ? report : null;
}

// Resolves to the Report to print, or null when printing/opening the overlay must be refused.
// Only this (awaitable) path can actually recalculate -- `beforeprint` (below) cannot.
export async function resolveReportForPrint(state) {
  if (!state.tool) return null;
  const { values, invalid } = currentValuesAndValidity(state.tool.fields);
  if (invalid) return null;
  if (!isStaleOnScreen()) return state.report;
  return recalculate(state.tool.name, values);
}

// `state.tool` is results.js's own `currentTool` shape (`{name, title, norm, fields,
// outputNodes}`) -- `buildRelazione`'s `data` contract wants `outputNodes`/`fields` at the top
// level alongside `tool`/`report`, so they are lifted out here rather than reshaping results.js's
// own state (shared with the interactive renderer, which does not otherwise need this flattening).
// `options` defaults to the complete §10 report; the overlay passes its own resolved §11 options.
export function buildPrintDocument(container, state, options = resolveOptions({})) {
  const { tool, report } = state;
  buildRelazione(container, { tool, report, outputNodes: tool ? tool.outputNodes : [], fields: tool ? tool.fields : [] }, options);
}

// `beforeprint` (Ctrl/Cmd+P the overlay's own keydown listener never got a chance to preventDefault
// on, File>Print, a right-click "Print"…) cannot await an async recalculation -- by the time it
// fires the OS print flow is already under way, so it can only use what is already known
// SYNCHRONOUSLY: the staleness flag `results.js` already maintains and client-side validity. When
// the overlay itself just built the print root (its own "Stampa / Salva PDF", `data-fresh="true"`)
// this is a no-op: the overlay's chosen §11 options must never be clobbered back to the complete
// default the instant the SAME `window.print()` call it made triggers this same event.
function handleBeforePrint() {
  const root = ensurePrintRoot();
  if (root.dataset.fresh === "true") {
    delete root.dataset.fresh;
    return;
  }
  clear(root);
  const state = getReportState();
  const { invalid } = currentValuesAndValidity(state.tool && state.tool.fields);
  if (!state.report || !state.tool || invalid || isStaleOnScreen()) {
    root.append(el("p", { class: "print-refusal", role: "alert", text: REFUSAL_TEXT }));
  } else {
    buildPrintDocument(root, state);
  }
}

function handleAfterPrint() {
  const root = document.getElementById(PRINT_ROOT_ID);
  if (root) clear(root);
}

window.addEventListener("beforeprint", handleBeforePrint);
window.addEventListener("afterprint", handleAfterPrint);
