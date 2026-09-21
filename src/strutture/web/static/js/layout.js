// Pane switch, mobile picker and focus management -- DESIGN_SPEC.md #2.
import { readJSON, writeJSON } from "./storage.js";

const NARROW_QUERY = "(max-width: 719.98px)";
const mediaQuery = window.matchMedia(NARROW_QUERY);

function els() {
  return {
    app: document.getElementById("app"),
    picker: document.querySelector(".app-picker"),
    index: document.getElementById("tool-index"),
    formPane: document.getElementById("form-pane"),
    resultsPane: document.getElementById("results-pane"),
    tabDati: document.getElementById("tab-dati"),
    tabRisultati: document.getElementById("tab-risultati"),
  };
}

// Single index implementation: moved between the desktop slot (direct child
// of #app, before #form-pane) and the mobile picker slot depending on the
// breakpoint, never duplicated.
function relocateIndex() {
  const { app, picker, index, formPane } = els();
  if (!app || !picker || !index || !formPane) return;
  if (mediaQuery.matches) {
    picker.append(index);
  } else {
    app.insertBefore(index, picker);
  }
}

export function isNarrow() {
  return mediaQuery.matches;
}

export function setPane(pane) {
  const { app, formPane, resultsPane, tabDati, tabRisultati } = els();
  if (!app) return;
  app.dataset.pane = pane;
  const showResults = pane === "risultati";
  if (formPane) formPane.hidden = isNarrow() && showResults;
  if (resultsPane) resultsPane.hidden = isNarrow() && !showResults;
  if (tabDati) tabDati.setAttribute("aria-selected", String(!showResults));
  if (tabRisultati) tabRisultati.setAttribute("aria-selected", String(showResults));
  writeJSON("sm.ui.pane", pane);
}

export function focusResults() {
  if (isNarrow()) setPane("risultati");
  const head = document.getElementById("results-head");
  if (head) head.focus({ preventScroll: false });
}

export function focusDati() {
  if (isNarrow()) setPane("dati");
  const title = document.getElementById("tool-title");
  if (title) title.focus({ preventScroll: false });
}

export function focusFirstError() {
  const invalid = document.querySelector('[aria-invalid="true"]');
  if (invalid) {
    if (isNarrow()) setPane("dati");
    invalid.focus({ preventScroll: false });
    return;
  }
  const summary = document.getElementById("error-summary");
  if (summary) summary.focus({ preventScroll: false });
}

function wireTabs() {
  const { tabDati, tabRisultati } = els();
  if (tabDati) tabDati.addEventListener("click", () => setPane("dati"));
  if (tabRisultati) tabRisultati.addEventListener("click", () => setPane("risultati"));
}

// Sticky bottom bar (<720px): shell owns the click-to-jump behaviour, the
// results package fills its text content via the verdict events/DOM writes.
function wireBottomBar() {
  const bar = document.getElementById("bottom-bar");
  if (bar) bar.addEventListener("click", () => setPane("risultati"));
}

// Header switch "Calcolo automatico" (WORKBENCH_SPEC #1/#2): persisted as
// sm.ui.live (default on), announced to the forms package through
// `strutture:live-setting {enabled}` on every change and once at boot.
function wireLiveSwitch() {
  const toggle = document.getElementById("live-toggle");
  if (!toggle) return;
  const enabled = readJSON("sm.ui.live", true);
  toggle.checked = enabled;
  const announce = (value) => document.dispatchEvent(new CustomEvent("strutture:live-setting", { detail: { enabled: value } }));
  toggle.addEventListener("change", () => {
    writeJSON("sm.ui.live", toggle.checked);
    announce(toggle.checked);
  });
  announce(enabled);
}

// Re-applies the current pane's hidden/visible state for the new breakpoint: `setPane`'s
// `formPane.hidden`/`resultsPane.hidden` depend on `isNarrow()`, so crossing 720px without a
// full reload (a window resize, a tablet rotation) must recompute them, not just move the index.
function handleBreakpointChange() {
  relocateIndex();
  setPane(document.getElementById("app")?.dataset.pane || "dati");
}

function init() {
  relocateIndex();
  mediaQuery.addEventListener("change", handleBreakpointChange);
  wireTabs();
  wireBottomBar();
  wireLiveSwitch();
  setPane(readJSON("sm.ui.pane", "dati"));
}

init();
