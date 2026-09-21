// Wiring only -- DESIGN_SPEC.md #5. Boot -> fetchTools -> index -> router.start();
// on route -> fetchSchema -> dispatch strutture:tool-schema; on run-request ->
// run-start -> runTool -> run-result; on results-rendered -> pane + focus.
import { fetchTools, fetchSchema, runTool } from "./api.js";
import { renderIndex } from "./tool-index.js";
import { readRoute, navigate, onRoute, start as startRouter } from "./router.js";
import { focusResults, focusFirstError } from "./layout.js";
import { el, clear } from "./dom.js";
// Side-effect imports: forms.js and results.js self-wire to the shared `strutture:*`
// events (DESIGN_SPEC.md #5) but are never called directly from here, so they must be
// imported for their module-level `document.addEventListener` registration to run.
import "./forms.js";
import "./results.js";

const indexRoot = document.getElementById("tool-index");
const formRoot = document.getElementById("form-root");
const toolTitleEl = document.getElementById("tool-title");
const runErrorEl = document.getElementById("run-error");

let tools = [];
let indexApi = null;

function dispatch(name, detail) {
  document.dispatchEvent(new CustomEvent(name, { detail }));
}

// Closes the mobile `<details class="app-picker">` after a choice and labels its `<summary>`
// with the current tool (DESIGN_SPEC §2): otherwise the full tool list stays open above the
// results sheet after every selection, and the closed summary only ever said "Strumenti".
function updatePicker(title) {
  const picker = document.querySelector(".app-picker");
  if (!picker) return;
  picker.open = false;
  const summary = picker.querySelector("summary");
  if (summary) summary.textContent = title ? `Strumenti — ${title}` : "Strumenti";
}

function showUnknownTool(name) {
  clear(formRoot);
  toolTitleEl.textContent = "Strumento sconosciuto";
  updatePicker("");
  formRoot.append(
    el("p", { text: `Strumento sconosciuto: ${name}` }),
    el("a", { href: "#/", text: "Torna all'elenco degli strumenti" }),
  );
}

function showNoTool() {
  clear(formRoot);
  toolTitleEl.textContent = "";
  updatePicker("");
  formRoot.append(el("p", { text: "Scegli uno strumento qui sopra." }));
}

async function selectTool(name, params) {
  const tool = tools.find((candidate) => candidate.name === name);
  if (!tool) {
    showUnknownTool(name);
    return;
  }
  runErrorEl.hidden = true;
  indexApi.setActive(name);
  toolTitleEl.textContent = tool.title;
  toolTitleEl.focus({ preventScroll: true });
  updatePicker(tool.title);

  let schema;
  try {
    schema = await fetchSchema(name);
  } catch (error) {
    clear(formRoot);
    formRoot.append(el("p", { text: "Impossibile caricare lo schema dello strumento." }));
    return;
  }
  dispatch("strutture:tool-schema", { ...schema, params });
}

function onRouteChange({ tool, params }) {
  if (!tool) {
    showNoTool();
    indexApi.setActive("");
    return;
  }
  selectTool(tool, params);
}

async function handleRunRequest(event) {
  const { name, values } = event.detail;
  dispatch("strutture:run-start", { name });
  try {
    const { status, report } = await runTool(name, values);
    if (status >= 500) {
      runErrorEl.hidden = false;
      runErrorEl.textContent = (report.errors && report.errors[0]) || "Errore del server.";
    } else {
      runErrorEl.hidden = true;
    }
    dispatch("strutture:run-result", { name, status, values, report });
  } catch (error) {
    runErrorEl.hidden = false;
    runErrorEl.textContent = "Impossibile contattare il server.";
    dispatch("strutture:run-network-error", { name, message: "Impossibile contattare il server." });
  }
}

function handleResultsRendered(event) {
  const { ok } = event.detail;
  if (ok) focusResults();
  else focusFirstError();
}

async function boot() {
  try {
    tools = await fetchTools();
  } catch (error) {
    tools = [];
  }
  indexApi = renderIndex(indexRoot, tools, {
    onSelect: (name) => navigate(name),
  });
  document.addEventListener("strutture:run-request", handleRunRequest);
  document.addEventListener("strutture:results-rendered", handleResultsRendered);
  onRoute(onRouteChange);
  startRouter();
}

boot();
