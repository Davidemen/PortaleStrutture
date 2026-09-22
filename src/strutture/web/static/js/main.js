// Wiring only -- DESIGN_SPEC.md #5 / WORKBENCH_SPEC.md #6. Boot -> fetchTools
// (existence check for routing; rail/home/palette fetch their own copies per
// the cross-package contract "rail/home read tools via api.fetchTools()") ->
// render rail -> router.start(); on route -> Home view or fetchSchema ->
// dispatch strutture:tool-schema; on run-request -> run-start -> runTool ->
// run-result; on results-rendered -> pane + focus.
import { fetchTools, fetchSchema, runTool } from "./api.js";
import { ensureCollegamenti } from "./usa-in.js";
import { ensureRiepilogo } from "./registro-stato.js";
import { renderIndex } from "./tool-index.js";
import { renderHome } from "./home.js";
import { initPalette } from "./palette.js";
import { initShortcuts } from "./shortcuts.js";
import { initProgettoPicker } from "./progetto-picker.js";
import { addRecent, siglaChip } from "./nav-state.js";
import { navigate, onRoute, start as startRouter } from "./router.js";
import { focusResults, focusFirstError } from "./layout.js";
import { unmountAnnullaUi } from "./annulla-ui.js";
import { el, clear } from "./dom.js";

const appEl = document.getElementById("app");
const indexRoot = document.getElementById("tool-index");
const homeRoot = document.getElementById("home-pane");
const registroRoot = document.getElementById("registro-pane");
const progettiRoot = document.getElementById("progetti-pane");
const variantiRoot = document.getElementById("varianti-pane");
const impostazioniRoot = document.getElementById("impostazioni-pane");
const progettoPickerRoot = document.getElementById("progetto-picker-root");
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
  unmountAnnullaUi();
  clear(formRoot);
  toolTitleEl.textContent = "";
  updatePicker("");
  if (bottomBarEl) bottomBarEl.hidden = true;
  indexApi.setActive("");
  renderHome(homeRoot, { onSelect: (name) => navigate(name) });
}

// #/registro (WORKBENCH_SPEC §13.1): a fixed rail destination, not a tool -- full-width page, no
// Dati/Sintesi split. Lazy-imported like the other packages' own dynamic imports below: a syntax
// error there must not take the rail/Home/palette down with it.
function showRegistro(params) {
  if (appEl) appEl.dataset.view = "registro";
  unmountAnnullaUi();
  clear(formRoot);
  toolTitleEl.textContent = "";
  updatePicker("");
  if (bottomBarEl) bottomBarEl.hidden = true;
  indexApi.setActive("registro");
  import("./registro.js")
    .then(({ renderRegistro }) => renderRegistro(registroRoot, { params }))
    .catch(() => {
      clear(registroRoot);
      registroRoot.append(el("p", { text: "Impossibile caricare il registro delle correzioni." }));
    });
}

// #/impostazioni (WORKBENCH_SPEC §26.8): a fixed rail destination like #/registro just above --
// full-width page, no Dati/Sintesi split.
function showImpostazioni(params) {
  if (appEl) appEl.dataset.view = "impostazioni";
  unmountAnnullaUi();
  clear(formRoot);
  toolTitleEl.textContent = "";
  updatePicker("");
  if (bottomBarEl) bottomBarEl.hidden = true;
  indexApi.setActive("impostazioni");
  import("./impostazioni.js")
    .then(({ renderImpostazioni }) => renderImpostazioni(impostazioniRoot, { params }))
    .catch(() => {
      clear(impostazioniRoot);
      impostazioniRoot.append(el("p", { text: "Impossibile caricare la pagina delle impostazioni." }));
    });
}

// #/progetti and #/progetti/<id> (WORKBENCH_SPEC §14.2/§14.3): fixed rail destinations, not tools
// -- same full-width, no Dati/Sintesi split pattern as #/registro just above. `router.js`'s own
// `tool` string carries the id as its second path segment ("progetti/<id>"), never a query param.
//
// Both routes render into the SAME `progettiRoot` node via a dynamic `import()` -- and a cold
// `import("./progetto.js")` (a bigger module graph: progetto-elementi.js, progetto-relazione.js,
// ...) measurably takes LONGER to resolve than an already-warm `import("./progetti.js")`, so two
// navigations fired moments apart (observed: create a project, `navigate()` straight to it, then
// immediately back to the list -- e.g. router.js's own same-tick hashchange/popstate coalescing
// still lets that pair through as two real, close-together dispatches) do not necessarily FINISH
// their imports in the order they were REQUESTED. `owner` is claimed HERE, synchronously, before
// either import even starts, so whichever call was requested LAST always wins regardless of which
// one's import happens to resolve last -- js/progetto.js's own `renderProgetto` (the one page here
// that awaits before finishing its first paint) checks it after that await and simply stops
// touching the DOM if a newer navigation already claimed the root.
function showProgetti(owner, view) {
  if (appEl) appEl.dataset.view = "progetti";
  unmountAnnullaUi();
  clear(formRoot);
  toolTitleEl.textContent = "";
  updatePicker("");
  if (bottomBarEl) bottomBarEl.hidden = true;
  indexApi.setActive("progetti");
  view()
    .catch(() => {
      if (progettiRoot._smOwner !== owner) return;
      clear(progettiRoot);
      progettiRoot.append(el("p", { text: "Impossibile caricare la pagina dei progetti." }));
    });
}

function showProgettiList() {
  const owner = {};
  progettiRoot._smOwner = owner;
  showProgetti(owner, () => import("./progetti.js").then(({ renderProgettiList }) => renderProgettiList(progettiRoot, { owner })));
}

function showProgettoPage(progettoId, params) {
  const owner = {};
  progettiRoot._smOwner = owner;
  showProgetti(owner, () => import("./progetto.js").then(({ renderProgetto }) => renderProgetto(progettiRoot, { progettoId, params, owner })));
}

// #/varianti/<tool> (WORKBENCH_SPEC §19.3, "Affianca"): same full-width, no Dati/Sintesi split
// slot as #/registro/#/progetti above, own `owner` guard for the same "two close navigations
// resolving out of order" reason as `showProgettoPage`.
function showVarianti(toolName) {
  const owner = {};
  variantiRoot._smOwner = owner;
  if (appEl) appEl.dataset.view = "varianti";
  unmountAnnullaUi();
  clear(formRoot);
  toolTitleEl.textContent = "";
  updatePicker("");
  if (bottomBarEl) bottomBarEl.hidden = true;
  indexApi.setActive("");
  import("./varianti-confronto.js")
    .then(({ renderVariantiConfronto }) => renderVariantiConfronto(variantiRoot, { tool: toolName, owner }))
    .catch(() => {
      if (variantiRoot._smOwner !== owner) return;
      clear(variantiRoot);
      variantiRoot.append(el("p", { text: "Impossibile caricare il confronto delle varianti." }));
    });
}

function showUnknownTool(name) {
  if (appEl) appEl.dataset.view = "tool";
  unmountAnnullaUi();
  clear(formRoot);
  toolTitleEl.textContent = "Strumento sconosciuto";
  updatePicker("");
  if (bottomBarEl) bottomBarEl.hidden = true;
  formRoot.append(
    el("p", { text: `Strumento sconosciuto: ${name}` }),
    el("a", { href: "#/", text: "Torna all'elenco degli strumenti" }),
  );
}

// A redundant `notify()` (router.js: hashchange+popstate for one logical navigation, coalesced
// there when they land in the same tick but NOT when a genuinely separate later navigation -- e.g.
// js/progetto-storia.js's "Carica questa revisione", `navigate()` away from a project page --
// still overlaps this function's own `await fetchSchema`) can start this async function again
// before the first call's `fetchSchema` has resolved. Both calls would otherwise go on to
// `dispatch("strutture:tool-schema", ...)`, rebuilding the form TWICE -- forms.js's own listener
// is synchronous, so this never doubles the DOM the way js/progetto.js's async render once did,
// but the SECOND dispatch reads `params` from whichever call it belongs to: a stale call for a
// PLAIN `#/<tool>` re-applies `initialValues` from localStorage/defaults, silently overwriting
// whatever a newer, more specific navigation (an `?elemento=`/`?anteprima=` deep link) had just
// asked to load. `token` makes only the LAST call to start ever allowed to dispatch.
let selectToolToken = 0;

async function selectTool(name, params) {
  const token = ++selectToolToken;
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
    if (token !== selectToolToken) return;
    unmountAnnullaUi();
    clear(formRoot);
    formRoot.append(el("p", { text: "Impossibile caricare lo schema dello strumento." }));
    return;
  }
  if (token !== selectToolToken) return;
  addRecent(name);
  dispatch("strutture:nav-state-changed");
  dispatch("strutture:tool-schema", { ...schema, params });
}

function onRouteChange({ tool, params }) {
  if (!tool) {
    showHome();
    return;
  }
  if (tool === "registro") {
    showRegistro(params);
    return;
  }
  if (tool === "progetti") {
    showProgettiList();
    return;
  }
  if (tool === "impostazioni") {
    showImpostazioni(params);
    return;
  }
  if (tool.startsWith("progetti/")) {
    showProgettoPage(tool.slice("progetti/".length), params);
    return;
  }
  if (tool.startsWith("varianti/")) {
    showVarianti(tool.slice("varianti/".length));
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
    import("./confronto.js"),
    import("./registro-indicator.js"),
    import("./dimensiona.js"),
    import("./sensibilita.js"),
  ]);
}

async function boot() {
  // Fire-and-forget, started before anything else awaits: the collegamenti registry (js/usa-in.js)
  // and the divergence riepilogo (js/registro-stato.js) begin loading immediately, in parallel with
  // `tools` and `loadSideEffectModules()` below, so both are very likely already cached by the time
  // the FIRST tool run completes -- an already-approved tool or one with consumers rarely flashes
  // its retired/missing controls on the first paint. Neither BLOCKS boot the way `tools` itself
  // does, though: a slow network must never delay the whole page becoming usable for the sake of
  // two secondary features, and results.js/forms.js re-check both caches on every render anyway,
  // so a first render that missed the cache simply catches up on the next one.
  ensureCollegamenti().catch(() => {});
  ensureRiepilogo().catch(() => {});
  try {
    tools = await fetchTools();
  } catch (error) {
    tools = [];
  }
  await loadSideEffectModules();
  indexApi = renderIndex(indexRoot, { onSelect: (name) => navigate(name) });
  initPalette({ onNavigate: (name) => navigate(name) });
  initShortcuts({ onHome: () => navigate(""), onImpostazioni: () => navigate("impostazioni") });
  initProgettoPicker(progettoPickerRoot);
  document.addEventListener("strutture:run-request", handleRunRequest);
  document.addEventListener("strutture:results-rendered", handleResultsRendered);
  onRoute(onRouteChange);
  startRouter();
}

boot();
