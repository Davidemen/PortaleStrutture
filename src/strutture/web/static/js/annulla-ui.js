// DOM/wiring half of "Annulla"/"Ripristina" (WORKBENCH_SPEC §21): the two action-bar buttons, the
// Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y keys (native-first while typing, see `nativeUndoWins`), the polite
// live region, and the per-tool `Map` of pure histories (js/annulla.js). Mounted once per
// `renderForm()` call by js/forms.js (`mountAnnullaUi`, same lazy-`getApi` pattern as
// js/elemento-salva.js/js/provenienza.js); the generic commit listeners below are wired ONCE at
// module load, not per mount, and always act on the "active" mount's state (mirrors js/forms.js's
// own module-level `current`) so a re-render never doubles them up.
import { el } from "./dom.js";
import { readValue } from "./fields.js";
import { formatValue } from "./format.js";
import { jumpToField } from "./campo-salto.js";
import { creaStoria, registra, annulla, ripristina, puoAnnullare, puoRipristinare, passoAnnulla, passoRipristina } from "./annulla.js";

const historyByTool = new Map(); // tool name -> storia (kept for the tab's life, WORKBENCH_SPEC §21.1)

let activeTool = null;
let activeFields = [];
let activeGetApi = null;
let lastKnownValues = null;
let applyingHistory = false; // true while WE are applying a snapshot: suppresses re-registering it
let activeRender = null; // set by the current mount; the generic listeners call it after a commit

function sameValue(a, b) {
  if (Array.isArray(a) || Array.isArray(b)) return JSON.stringify(a) === JSON.stringify(b);
  return a === b;
}

function sameValues(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function formatFieldValue(field, value) {
  if (value === null || value === undefined) return "—";
  if (field && field.kind === "boolean") return value ? "sì" : "no";
  if (field && field.kind === "number" && typeof value === "number") return formatValue(value).text;
  return String(value);
}

// The step to record for a values change: a single changed scalar field gets a "<label> <old> →
// <new> <unit>" description (the tooltip sample in §21.1); a table/list field (many rows can
// change at once -- one paste, one row op) names the field instead of trying to show its values; a
// change touching more than one field (Azzera dati resets every field at once) falls back to a
// generic label. `forcedLabel` (Carica esempio) always wins outright. Returns null when nothing
// actually changed (a "change" event that round-tripped back to the same value).
function describePasso(fields, oldValues, newValues, forcedLabel) {
  const changed = fields.filter((f) => !sameValue(oldValues ? oldValues[f.name] : undefined, newValues[f.name])).map((f) => f.name);
  if (forcedLabel) return { etichetta: forcedLabel, testo: forcedLabel, campo: null };
  if (changed.length === 0) return null;
  if (changed.length > 1) return { etichetta: "Modifica dati", testo: "Modifica dati", campo: null };
  const field = fields.find((f) => f.name === changed[0]);
  const etichetta = (field && field.label) || changed[0];
  if (field && (field.kind === "table" || field.kind === "list")) {
    return { etichetta, testo: etichetta, campo: field.name };
  }
  const prima = formatFieldValue(field, oldValues ? oldValues[changed[0]] : undefined);
  const dopo = formatFieldValue(field, newValues[changed[0]]);
  const unit = field && field.unit ? ` ${field.unit}` : "";
  return { etichetta, testo: `${etichetta} ${prima} → ${dopo}${unit}`, campo: field ? field.name : null };
}

function tryCommit(explicitLabel) {
  if (applyingHistory || !activeTool || !activeGetApi) return;
  const api = activeGetApi();
  if (!api) return;
  const newValues = api.allValues();
  if (lastKnownValues && sameValues(lastKnownValues, newValues)) return;
  const passo = describePasso(activeFields, lastKnownValues, newValues, explicitLabel);
  if (!passo) return;
  const storia = historyByTool.get(activeTool) || creaStoria(lastKnownValues || newValues);
  historyByTool.set(activeTool, registra(storia, { ...passo, valori: newValues }));
  lastKnownValues = newValues;
  if (activeRender) activeRender();
}

// Applies a stored snapshot exactly like a manual edit (§21.1): `api.setValues()` then ONE `change`
// dispatch, so js/forms.js's own `handleChange` runs unchanged (validation, persistence, live run,
// redraw). `applyingHistory` stops that dispatch from being re-recorded as a brand new step.
function applicaValori(valori, verbo, etichetta, campo) {
  const api = activeGetApi && activeGetApi();
  if (!api) return;
  applyingHistory = true;
  api.setValues(valori);
  lastKnownValues = valori;
  const form = document.getElementById("tool-form");
  if (form) form.dispatchEvent(new Event("change", { bubbles: true }));
  applyingHistory = false;
  if (activeRender) activeRender();
  announce(`${verbo}: ${etichetta}`);
  // §21.1 asks only for the section to open and the field to flash, not for the keyboard focus to
  // move -- someone who reached "Annulla"/"Ripristina" with the keyboard (Enter/Space) would
  // otherwise lose focus off the button and be unable to press it again right away.
  if (campo) jumpToField(campo, { focus: false });
}

function doUndo() {
  const storia = historyByTool.get(activeTool);
  if (!storia || !puoAnnullare(storia)) return;
  const passo = passoAnnulla(storia);
  historyByTool.set(activeTool, annulla(storia));
  applicaValori(historyByTool.get(activeTool).presente, "Annullato", passo.etichetta, passo.campo);
}

function doRedo() {
  const storia = historyByTool.get(activeTool);
  if (!storia || !puoRipristinare(storia)) return;
  const passo = passoRipristina(storia);
  historyByTool.set(activeTool, ripristina(storia));
  applicaValori(historyByTool.get(activeTool).presente, "Ripristinato", passo.etichetta, passo.campo);
}

let liveRegion = null;
function announce(text) {
  if (liveRegion) liveRegion.textContent = text;
}

// A dialog or popover open anywhere on the page (§11 overlay, §18 sketch popover, §14 project
// dialogs): the keys do nothing at all, native or app-handled (§21.1).
function overlayOpen() {
  // `role="dialog"` alone is not enough: the command palette (js/palette.js) and the rail
  // flyouts (js/rail-flyout.js) keep their dialog markup in the DOM at all times, just hidden by
  // an ancestor's `hidden` attribute -- `offsetParent` is null for anything CSS `display:none`
  // hides, same check js/nav-state.js's own `trapFocus` already uses for "is this reachable".
  return Array.from(document.querySelectorAll('dialog[open], [role="dialog"]')).some((node) => node.offsetParent !== null);
}

// The focused control still holds UNCOMMITTED typing (its live value differs from the last
// confirmed snapshot): the key is left to the browser for character-level undo inside the box
// (§21.1 "native undo first"). Only plain scalar Dati controls are considered -- a table cell has
// no top-level field name of its own and always falls to the app-handled branch.
function nativeUndoWins() {
  const active = document.activeElement;
  if (!active || (active.tagName !== "INPUT" && active.tagName !== "TEXTAREA")) return false;
  const field = activeFields.find((f) => f.name === active.name);
  // No top-level Dati field matches this control's `name`: either a table cell (no `name` of its
  // own, §21.1 keeps those app-handled -- see `test_table_paste_is_one_step`) or a free-text
  // control with no field at all (the "Incolla da Excel" textarea). A table cell always sits
  // inside a `<table>`; anything else defers to native undo rather than risk hijacking it.
  if (!field) return active.tagName === "TEXTAREA" || !active.closest("table");
  const form = document.getElementById("tool-form");
  if (!form) return false;
  return !sameValue(lastKnownValues ? lastKnownValues[field.name] : undefined, readValue(form, field));
}

// A text-editable control (INPUT/TEXTAREA/SELECT) that lives OUTSIDE both the live #tool-form
// (dialogs and popovers included -- §18 sketch edit, the paste-table dialog) and its action bar
// (#form-actions: rendered as a SIBLING of `<form id="tool-form">`, associated to it only via the
// `form=` attribute): Home's search box, Registro/Progetti filters and notes, the project
// selector, relazione options. The key is left to the browser entirely there, never even
// inspected for an undo/redo match (§21.1 "native undo first" is not just about mid-edit typing --
// it is about every text control that is not part of Dati). Anything else -- a BUTTON, the results
// pane heading a live run moves focus to after Tab, `document.body` with nothing focused -- carries
// no text-editing risk, so it is left to the normal app-handled path below.
function isForeignEditable(node) {
  if (!node) return false;
  if (node.tagName !== "INPUT" && node.tagName !== "TEXTAREA" && node.tagName !== "SELECT") return false;
  const form = document.getElementById("tool-form");
  if (form && form.isConnected && (node === form || form.contains(node))) return false;
  const actions = document.getElementById("form-actions");
  if (actions && actions.isConnected && (node === actions || actions.contains(node))) return false;
  return true;
}

document.addEventListener("keydown", (event) => {
  if (event.defaultPrevented || !(event.ctrlKey || event.metaKey)) return;
  const key = event.key.toLowerCase();
  const isUndo = key === "z" && !event.shiftKey;
  const isRedo = (key === "z" && event.shiftKey) || key === "y";
  if (!isUndo && !isRedo) return;
  if (isForeignEditable(document.activeElement)) return;
  if (overlayOpen() || nativeUndoWins()) return;
  event.preventDefault();
  if (isUndo) doUndo();
  else doRedo();
});

// Native `change` (typing committed on blur, a select/checkbox, a table cell edit or the
// synthetic `change` js/table-input-events.js fires after a paste/row op) -- one commit per event,
// which is already "one step per confirmed edit" since the browser itself only fires `change` once
// per control per edit session. `form.dataset.annullaLabel` lets js/forms.js name a step outright
// (Azzera dati) without this module needing to special-case that button.
document.addEventListener("change", (event) => {
  const form = event.target.closest ? event.target.closest("#tool-form") : null;
  if (!form) return;
  const label = form.dataset.annullaLabel || null;
  delete form.dataset.annullaLabel;
  tryCommit(label);
});

// Safety net for a control whose value was set programmatically (js/number-input.js's Up/Down
// stepper only dispatches `input`, never a native `change`, since it never receives real keyboard
// text entry): closing the step on focus leaving the control either way, per §21.1.
document.addEventListener(
  "focusout",
  (event) => {
    const form = event.target.closest ? event.target.closest("#tool-form") : null;
    if (form) tryCommit(null);
  },
  true,
);

// Carica esempio applies every field programmatically (no native event at all, js/forms.js) and
// then dispatches this instead -- decoupled from `change` so it can never double-trigger
// js/forms.js's own `handleChange`/`requestRun`, which "Carica esempio" already calls itself.
document.addEventListener("strutture:annulla-commit", (event) => {
  tryCommit((event.detail && event.detail.label) || null);
});

function renderInto(undoBtn, redoBtn) {
  const storia = historyByTool.get(activeTool) || creaStoria(lastKnownValues || {});
  const undo = passoAnnulla(storia);
  const redo = passoRipristina(storia);
  undoBtn.setAttribute("aria-disabled", String(!undo));
  undoBtn.title = undo ? `Annulla: ${undo.testo}` : "";
  redoBtn.setAttribute("aria-disabled", String(!redo));
  redoBtn.title = redo ? `Ripristina: ${redo.testo}` : "";
}

// Mounted by js/forms.js's `renderForm`, right after "Carica esempio" (§21.1 action-bar order).
// `getApi` is the same temporal-dead-zone-safe accessor js/elemento-salva.js/js/provenienza.js use
// (`api` is still a few statements away at mount time) -- the resume-or-start-empty decision
// (§21.1 "coming back to a tool") waits one microtask for the same reason, then reads
// `api.allValues()` once it is guaranteed to exist.
export function mountAnnullaUi({ tool, fields, getApi }) {
  activeTool = tool;
  activeFields = fields;
  activeGetApi = getApi;
  lastKnownValues = null;

  const undoBtn = el("button", { type: "button", class: "an-btn", "aria-label": "Annulla modifica", "aria-disabled": "true", text: "↶ Annulla" });
  const redoBtn = el("button", { type: "button", class: "an-btn", "aria-label": "Ripristina modifica", "aria-disabled": "true", text: "↷ Ripristina" });
  // `role="status"` alone (no `aria-live` attribute): implicitly a polite live region for
  // assistive tech, but DESIGN_SPEC §3 fixes EXACTLY 3 `[aria-live]`/`[role=alert]` elements
  // app-wide (`test_no_console_errors_no_csp`, a permanent test) -- js/elemento-salva.js's own
  // status text uses the identical `role="status"`-only trick for the same reason.
  liveRegion = el("p", { class: "an-live", role: "status" });
  undoBtn.addEventListener("click", () => {
    if (undoBtn.getAttribute("aria-disabled") !== "true") doUndo();
  });
  redoBtn.addEventListener("click", () => {
    if (redoBtn.getAttribute("aria-disabled") !== "true") doRedo();
  });
  activeRender = () => renderInto(undoBtn, redoBtn);
  activeRender();

  Promise.resolve().then(() => {
    if (activeTool !== tool) return; // superseded by a later mount before this microtask ran
    const api = getApi();
    if (!api) return;
    const valori = api.allValues();
    const existing = historyByTool.get(tool);
    historyByTool.set(tool, existing && sameValues(existing.presente, valori) ? existing : creaStoria(valori));
    lastKnownValues = valori;
    activeRender();
  });

  return el("div", { class: "an-widget" }, [undoBtn, redoBtn, liveRegion]);
}

// The boundaries that reset the history outright (§21.1): opening `?elemento=`, "Ricarica" in the
// 409 dialog, "Carica questa revisione" (`?anteprima=1`), a "Usa in…" arrival. Each caller applies
// its own values via `api.setValues()` first, then calls this -- undoing past a load must never put
// another element's inputs under the loaded element's header (§21.1 rationale).
// Called by js/main.js right before it empties #form-root for Home/Registro/Progetti (any
// destination that is not a tool): without this, `activeTool`/`activeGetApi` kept pointing at the
// just-unmounted tool's module-level `api`, so a Ctrl+Z pressed from one of those pages (or after
// returning to the SAME tool later, before its first mount microtask ran) applied a step to a form
// that no longer exists and silently consumed it from the history.
export function unmountAnnullaUi() {
  activeTool = null;
  activeFields = [];
  activeGetApi = null;
  lastKnownValues = null;
  activeRender = null;
  liveRegion = null;
}

export function azzeraStoriaAnnulla() {
  if (!activeTool || !activeGetApi) return;
  const api = activeGetApi();
  if (!api) return;
  const valori = api.allValues();
  historyByTool.set(activeTool, creaStoria(valori));
  lastKnownValues = valori;
  if (activeRender) activeRender();
}
