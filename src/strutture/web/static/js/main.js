// Wiring only -- DESIGN_SPEC.md #5 / WORKBENCH_SPEC.md #6. Boot -> fetchTools
// (existence check for routing; rail/home/palette fetch their own copies per
// the cross-package contract "rail/home read tools via api.fetchTools()") ->
// render rail -> router.start(); on route -> Home view or fetchSchema ->
// dispatch strutture:tool-schema; on run-request -> run-start -> runTool ->
// run-result; on results-rendered -> pane + focus.
import { fetchTools, fetchSchema, runTool } from "./api.js";
import { renderIndex } from "./tool-index.js";
import { renderHome } from "./home.js";
import { initPalette } from "./palette.js";
import { initShortcuts } from "./shortcuts.js";
import { addRecent, siglaChip } from "./nav-state.js";
import { navigate, onRoute, start as startRouter } from "./router.js";
import { focusResults, focusFirstError } from "./layout.js";
import { el, clear } from "./dom.js";

const appEl = document.getElementById("app");
const indexRoot = document.getElementById("tool-index");
const homeRoot = document.getElementById("home-pane");
const formRoot = document.getElementById("form-root");
const toolTitleEl = document.getElementById("tool-title");
const runErrorEl = document.getElementById("run-error");
const bottomBarEl = document.getElementById("bottom-bar");

let tools = [];
let indexApi = null;

function dispatch(name, detail) {
  document.dispatchEvent(new CustomEvent(name, { detail }));
}

// Labels the mobile `<details class="app-picker">`'s `<summary>` with the current tool
// (DESIGN_SPEC §2: the closed summary only ever said "Strumenti" otherwise) and, only when a
// tool was actually just PICKED (`close: true`, from `selectTool` below), closes it: otherwise
// the full tool list stays open above the results sheet after every selection. `showHome`/
// `showUnknownTool` must NOT force it closed -- boot() calls `startRouter()` (-> `showHome()`)
// asynchronously after `fetchTools()`/dynamic imports resolve, and forcing the picker closed
// there raced an early user click on it wide open (observed: `test_mobile_flow` losing that race
// under the fuller `loadSideEffectModules()` import graph, closing a picker the user had just
// opened, with nothing left to ever reopen it).
function updatePicker(title, { close = false } = {}) {
  const picker = document.querySelector(".app-picker");
  if (!picker) return;
  if (close) picker.open = false;
  const summary = picker.querySelector("summary");
  if (summary) summary.textContent = title ? `Strumenti — ${title}` : "Strumenti";
}

function showHome() {
  if (appEl) appEl.dataset.view = "home";
  clear(formRoot);
  toolTitleEl.textContent = "";
  updatePicker("");
  if (bottomBarEl) bottomBarEl.hidden = true;
  indexApi.setActive("");
  renderHome(homeRoot, { onSelect: (name) => navigate(name) });
}

function showUnknownTool(name) {
  if (appEl) appEl.dataset.view = "tool";
  clear(formRoot);
  toolTitleEl.textContent = "Strumento sconosciuto";
  updatePicker("");
  if (bottomBarEl) bottomBarEl.hidden = true;
  formRoot.append(
    el("p", { text: `Strumento sconosciuto: ${name}` }),
    el("a", { href: "#/", text: "Torna all'elenco degli strumenti" }),
  );
}

async function selectTool(name, params) {
  const tool = tools.find((candidate) => candidate.name === name);
  if (!tool) {
    showUnknownTool(name);
    return;
  }
  if (appEl) appEl.dataset.view = "tool";
  runErrorEl.hidden = true;
  indexApi.setActive(name);
  clear(toolTitleEl);
  toolTitleEl.append(siglaChip(tool.sigla), ` ${tool.title}`);
  toolTitleEl.focus({ preventScroll: true });
  updatePicker(tool.title, { close: true });
  if (bottomBarEl) bottomBarEl.hidden = false;

  let schema;
  try {
    schema = await fetchSchema(name);
  } catch (error) {
    clear(formRoot);
    formRoot.append(el("p", { text: "Impossibile caricare lo schema dello strumento." }));
    return;
  }
  addRecent(name);
  dispatch("strutture:nav-state-changed");
  dispatch("strutture:tool-schema", { ...schema, params });
}

function onRouteChange({ tool, params }) {
  if (!tool) {
    showHome();
    return;
  }
  selectTool(tool, params);
}

async function handleRunRequest(event) {
  const { name, values, reason } = event.detail;
  dispatch("strutture:run-start", { name, reason });
  try {
    const { status, report } = await runTool(name, values);
    if (status >= 500) {
      runErrorEl.hidden = false;
      runErrorEl.textContent = (report.errors && report.errors[0]) || "Errore del server.";
    } else {
      runErrorEl.hidden = true;
    }
    dispatch("strutture:run-result", { name, status, values, report, reason });
  } catch (error) {
    runErrorEl.hidden = false;
    runErrorEl.textContent = "Impossibile contattare il server.";
    dispatch("strutture:run-network-error", { name, message: "Impossibile contattare il server.", reason });
  }
}

// WORKBENCH_SPEC #4 seam: moving focus/scroll to the results sheet on every run fights the
// live-recalculation scroll-preservation results.js already does (WORKBENCH_SPEC #2) -- an
// engineer mid-keystroke should never be yanked away from the field they are typing in. Only an
// explicit run ("manual" = Calcola/Enter/Ctrl+Enter, "example" = Carica esempio) steals focus;
// "live" (debounced typing) never does, regardless of outcome.
function handleResultsRendered(event) {
  const { ok, reason } = event.detail;
  if (reason === "live") return;
  if (ok) focusResults();
  else focusFirstError();
}

// Side-effect imports: forms.js and results.js self-wire to the shared `strutture:*`
// events (DESIGN_SPEC.md #5) but are never called directly from here, so they must be
// imported for their module-level `document.addEventListener` registration to run.
// Dynamic + caught (Promise.allSettled): forms-live and results-workbench build these
// files in parallel and cannot talk to this package -- a syntax/import error on their
// side must not take down the rail, Home or the palette (a static `import` of a broken
// module fails the whole graph, including this file).
async function loadSideEffectModules() {
  await Promise.allSettled([
    import("./forms.js"),
    import("./results.js"),
    import("./relazione-print.js"),
    import("./relazione-overlay.js"),
  ]);
}

async function boot() {
  try {
    tools = await fetchTools();
  } catch (error) {
    tools = [];
  }
  await loadSideEffectModules();
  indexApi = renderIndex(indexRoot, { onSelect: (name) => navigate(name) });
  initPalette({ onNavigate: (name) => navigate(name) });
  initShortcuts({ onHome: () => navigate("") });
  document.addEventListener("strutture:run-request", handleRunRequest);
  document.addEventListener("strutture:results-rendered", handleResultsRendered);
  onRoute(onRouteChange);
  startRouter();
}

boot();
