// "Usa in..." -- typed links between tools (WORKBENCH_SPEC §15). The results-toolbar button
// (js/results-toolbar.js builds `.ui-toggle` only when js/results.js's own gate says so: the run
// succeeded and `per_strumento[tool].usa_in` is non-empty) opens a small menu listing the consumer
// tools; choosing one resolves this tool's OWN `fornisce` keys against its last successful report
// and navigates to `#/<consumer>?da=<tool>&<chiave>=<valore>&...` -- js/provenienza.js reads that
// same query on the consumer side. The registry (`GET /api/tools/collegamenti`) is fetched ONCE,
// at boot (js/main.js calls `ensureCollegamenti` alongside `fetchTools`), so it is already
// synchronously available by the FIRST render -- same reasoning as js/registro-stato.js's own
// riepilogo prefetch. The last successful report is tracked here directly, off `strutture:run-
// result`, rather than imported from js/results.js: that avoids a module cycle (results.js reads
// `usaInFor` from here to decide whether to show the button at all).
import { el } from "./dom.js";
import { fetchTools } from "./api.js";
import { readPath } from "./output-schema.js";
import { navigate } from "./router.js";
import { siglaChip } from "./nav-state.js";
import { ensureCollegamenti, collegamentiSnapshot } from "./collegamenti-api.js";
import { loadedElementState } from "./elemento-salva.js";

export { ensureCollegamenti };

let toolsPromise = null; // cached fetchTools(), for the menu's sigla chips + titles
let lastSuccessful = { name: null, report: null };

// Synchronous: `[]` before the registry has loaded, or for a tool with no consumers.
export function usaInFor(toolName) {
  const registry = collegamentiSnapshot();
  const entry = registry && registry.per_strumento[toolName];
  return entry ? entry.usa_in : [];
}

// The `{chiave: valore}` `toolName`'s run `report` offers to its consumers -- forwarded inputs
// from `inputs_echo`, output values from `data` -- resolved from the registry's own `fornitori`
// paths client-side (WORKBENCH_SPEC §15: "resolve the paths client-side from the registry"). Skips
// a key whose value is null/undefined rather than sending an empty param.
function resolvedValues(toolName, report) {
  const registry = collegamentiSnapshot();
  if (!registry) return {};
  const entry = registry.per_strumento[toolName];
  const fornisce = (entry && entry.fornisce) || [];
  const echo = (report && report.inputs_echo) || {};
  const data = (report && report.data) || {};
  const out = {};
  for (const chiave of fornisce) {
    const link = registry.chiavi[chiave];
    const fornitore = link && link.fornitori.find((f) => f.strumento === toolName);
    if (!fornitore) continue;
    const value = fornitore.ingresso ? readPath(echo, fornitore.percorso) : readPath(data, fornitore.percorso);
    if (value === null || value === undefined) continue;
    out[chiave] = value;
  }
  return out;
}

function ensureTools() {
  if (!toolsPromise) {
    toolsPromise = fetchTools().catch((error) => {
      toolsPromise = null;
      throw error;
    });
  }
  return toolsPromise;
}

function closeMenu() {
  const menu = document.querySelector(".ui-menu");
  if (menu) menu.remove();
  const button = document.querySelector(".ui-toggle");
  if (button) button.setAttribute("aria-expanded", "false");
}

// WORKBENCH_SPEC §25.1: `elemento_id`/`revisione_fornitore` are added only when the on-screen
// provider EXACTLY matches a saved element -- no unsaved changes (the §14.1 "dati modificati"
// state, read here off the SAME sintesi js/elemento-sintesi.js would save) and it IS a saved
// element (`loadedElementState`, never an unsaved `?anteprima=1` preview). When it does not
// match, the link carries no `da_elemento` ("origine non salvata" in the tooltip elsewhere).
function navigateToConsumer(providerName, consumerName) {
  if (lastSuccessful.name !== providerName || !lastSuccessful.report) return;
  const values = resolvedValues(providerName, lastSuccessful.report);
  const params = { da: providerName };
  for (const [chiave, value] of Object.entries(values)) params[chiave] = String(value);
  // §25.1: exactly "the on-screen provider matches the saved revision" -- `loaded.modificato`
  // (elemento-salva.js's own footprint of the inputs it was last saved/reloaded with) is the
  // real test; a run finishing successfully says nothing about whether those inputs were ever
  // saved at all (e.g. a field changed after loading ?elemento=X, calc settled, still unsaved).
  const loaded = loadedElementState(providerName);
  if (loaded && !loaded.modificato) {
    params.da_elemento = loaded.id;
    params.da_revisione = String(loaded.revisione);
  }
  navigate(consumerName, params);
}

function buildMenuItem(tool, consumerName, providerName) {
  const label = tool ? tool.title : consumerName;
  const item = el("button", { type: "button", class: "ui-menu-item", role: "menuitem", "data-tool": consumerName }, [
    tool ? siglaChip(tool.sigla) : siglaChip("?"),
    document.createTextNode(` ${label}`),
  ]);
  item.addEventListener("click", () => {
    closeMenu();
    navigateToConsumer(providerName, consumerName);
  });
  return item;
}

async function openMenu(button, providerName) {
  closeMenu();
  const consumerNames = usaInFor(providerName);
  if (consumerNames.length === 0) return;
  let tools = [];
  try {
    tools = await ensureTools();
  } catch (error) {
    tools = [];
  }
  // The page could have moved on (a different tool run, or navigated away) while this awaited.
  if (!document.body.contains(button) || button !== document.querySelector(".ui-toggle")) return;
  const toolsByName = new Map(tools.map((tool) => [tool.name, tool]));
  const menu = el("div", { class: "ui-menu", role: "menu" });
  for (const name of consumerNames) menu.append(buildMenuItem(toolsByName.get(name), name, providerName));
  button.insertAdjacentElement("afterend", menu);
  button.setAttribute("aria-expanded", "true");
  const first = menu.querySelector(".ui-menu-item");
  if (first) first.focus();
  menu.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    event.preventDefault();
    closeMenu();
    button.focus();
  });
}

function wireButton(button, providerName) {
  button.onclick = () => {
    const open = button.getAttribute("aria-expanded") === "true";
    if (open) closeMenu();
    else openMenu(button, providerName);
  };
}

// Click outside the menu (and outside the button that opened it) closes it -- registered once,
// at module load, never per-render: `.ui-toggle`/`.ui-menu` are looked up fresh on every call, so
// this never goes stale across a toolbar rebuild.
document.addEventListener("click", (event) => {
  const menu = document.querySelector(".ui-menu");
  if (!menu) return;
  if (menu.contains(event.target) || event.target.closest(".ui-toggle")) return;
  closeMenu();
});

document.addEventListener("strutture:run-result", (event) => {
  const { name, report } = event.detail || {};
  if (report && report.ok) lastSuccessful = { name, report };
});

// js/results-toolbar.js rebuilds a FRESH `.ui-toggle` node on every render (live or manual) --
// re-wiring here on every `results-rendered` is what makes the button keep working across those
// rebuilds instead of losing its click handler the instant results.js repaints (same pattern
// js/confronto.js uses for `.cf-toggle`).
document.addEventListener("strutture:results-rendered", (event) => {
  const { name } = event.detail || {};
  const button = document.querySelector(".ui-toggle");
  if (button) wireButton(button, name);
  else closeMenu();
});
