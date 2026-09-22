// Live calculation engine -- WORKBENCH_SPEC §2. Listens for `strutture:inputs-changed` (forms.js,
// plus the single table-edit hook in table-input-events.js) and `strutture:tool-schema`; decides
// whether/when to run, and is the sole dispatcher of `strutture:run-request`. main.js (shell)
// stays the sole executor of the actual fetch (unchanged run-request -> run-start -> runTool ->
// run-result pipeline) -- live.js never calls the network itself, so a live-triggered run and a
// manual "Calcola" can never race into a double fetch.
//
// "One request in flight per tool" is achieved by queueing (a newer trigger while one is already
// in flight waits and fires with the LATEST values the instant the in-flight one settles) rather
// than an AbortController: main.js/api.js (shell package, out of forms-live's file ownership) do
// not thread a per-request `AbortSignal` through `runTool`, so there is nothing in live.js's own
// files to attach one to. Queueing gives the same observable guarantee -- a stale response can
// never land after, and so never overwrite, a fresher one -- without needing that cross-package
// change; see the final report for this as a documented contract deviation.
import { readJSON } from "./storage.js";
import { describeFields } from "./schema.js";
import { validateValues } from "./validate.js";
import { visibleValues } from "./forms-sections.js";

const DEBOUNCE_MS = 300;
const SLOW_RUN_MS = 800;
const MAX_LIVE_TABLE_ROWS = 200;
const LIVE_SETTING_KEY = "sm.ui.live";

function initialSession() {
  return {
    name: null,
    fields: [],
    metaLive: true,
    headerLive: readJSON(LIVE_SETTING_KEY, true),
    lastElapsedMs: 0,
    debounceTimer: null,
    inFlight: false,
    pending: null,
    lastRequestAt: null,
  };
}

let session = initialSession();

function currentForm() {
  return document.querySelector("#form-root form");
}

function dispatch(name, detail) {
  document.dispatchEvent(new CustomEvent(name, { detail, bubbles: true }));
}

function markStale() {
  if (session.name) dispatch("strutture:results-stale", { name: session.name });
}

function hasLargeTable(values) {
  return Object.values(values || {}).some((value) => Array.isArray(value) && value.length > MAX_LIVE_TABLE_ROWS);
}

// WORKBENCH_SPEC §2 "when live is off" gate.
function isLiveOn(values) {
  if (session.metaLive === false) return false;
  if (!session.headerLive) return false;
  if (session.lastElapsedMs > SLOW_RUN_MS) return false;
  if (hasLargeTable(values)) return false;
  return true;
}

// Exported so forms.js can decide whether to show the "Calcola" button (only shown when live is
// off, WORKBENCH_SPEC §3) without duplicating the gate logic.
export function isLiveEnabled(values) {
  return isLiveOn(values || {});
}

// WORKBENCH_SPEC §20.1: "Salva" waits for a pending/in-flight live run (at most the debounce +
// one run) so the saved summary belongs to the saved inputs. Resolves once neither a debounce
// timer nor an in-flight/queued run remains for the CURRENT tool; resolves immediately when there
// is nothing to wait for (live off, or no session at all).
export function whenSettled() {
  return new Promise((resolve) => {
    function poll() {
      if (session.debounceTimer == null && !session.inFlight && !session.pending) {
        resolve();
        return;
      }
      setTimeout(poll, 20);
    }
    poll();
  });
}

function clearDebounce() {
  if (session.debounceTimer != null) clearTimeout(session.debounceTimer);
  session = { ...session, debounceTimer: null };
}

function fireRun(name, values, reason) {
  session = { ...session, inFlight: true, lastRequestAt: performance.now() };
  dispatch("strutture:run-request", { name, values, reason });
}

function completeInFlight() {
  const pending = session.pending;
  session = { ...session, inFlight: false, pending: null };
  if (pending) fireRun(session.name, pending.values, pending.reason);
}

// The single entry point that actually triggers a run: the debounce timer below, Enter/Ctrl+Enter,
// "Carica esempio" and the "Calcola" button (forms.js calls this last pair directly) all funnel
// through here so every run -- live or manual -- shares the same one-in-flight bookkeeping.
export function requestRun(name, values, reason) {
  if (!name) return;
  clearDebounce();
  if (session.inFlight) {
    session = { ...session, pending: { values, reason } };
    return;
  }
  fireRun(name, values, reason);
}

function scheduleLiveRun(name, values) {
  const timer = setTimeout(() => requestRun(name, values, "live"), DEBOUNCE_MS);
  session = { ...session, debounceTimer: timer };
}

// `detail.valid`, when the caller already computed it (forms.js's field-level dispatch), is
// trusted; the table hook dispatches a bare ping with no detail, so it is re-derived here from
// the live DOM -- which also means an async CSV/MIDAS-import completion is picked up correctly
// even though the ping itself may fire a tick before the rows finish loading.
function handleInputsChanged(event) {
  if (!session.name) return;
  const detail = event.detail || {};
  if (detail.name && detail.name !== session.name) return;
  const form = currentForm();
  if (!form) return;
  const values = detail.values && typeof detail.valid === "boolean" ? detail.values : visibleValues(form, session.fields);
  const valid = typeof detail.valid === "boolean" ? detail.valid : Object.keys(validateValues(session.fields, values)).length === 0;
  clearDebounce();
  session = { ...session, pending: null };
  if (!valid) {
    markStale(); // "dati non validi -- risultati precedenti" (results package renders the chip)
    return;
  }
  if (!isLiveOn(values)) {
    markStale(); // live is off and inputs are newer than results -> "Dati modificati -- premi Calcola"
    return;
  }
  scheduleLiveRun(session.name, values);
}

document.addEventListener("strutture:inputs-changed", handleInputsChanged);

document.addEventListener("strutture:tool-schema", (event) => {
  const { name, input, live } = event.detail || {};
  session = { ...initialSession(), name, fields: describeFields(input || {}), metaLive: live !== false };
  if (manualRunPending) {
    manualRunPending = false;
    setTimeout(manualRun, 0); // after forms.js's own listener has mounted and restored the form
  }
});

document.addEventListener("strutture:live-setting", (event) => {
  session = { ...session, headerLive: Boolean(event.detail && event.detail.enabled) };
});

document.addEventListener("strutture:run-result", (event) => {
  const { name, values } = event.detail || {};
  if (name !== session.name) return;
  if (session.lastRequestAt != null) session = { ...session, lastElapsedMs: performance.now() - session.lastRequestAt };
  completeInFlight();
});

document.addEventListener("strutture:run-network-error", (event) => {
  if (!event.detail || event.detail.name !== session.name) return;
  completeInFlight();
});

// Ctrl+Enter runs immediately from anywhere (WORKBENCH_SPEC §2); Enter-in-a-field already submits
// the native form, which forms.js routes through `requestRun` too.
// A press that lands before the tool's schema has arrived (a reload: the title shows first, the
// schema a fetch later) is remembered and fired once the form is mounted, instead of being lost.
let manualRunPending = false;

function manualRun() {
  if (!session.name) {
    manualRunPending = true;
    return;
  }
  const form = currentForm();
  if (!form) return;
  const values = visibleValues(form, session.fields);
  if (Object.keys(validateValues(session.fields, values)).length > 0) return; // already shown inline
  requestRun(session.name, values, "manual");
}

document.addEventListener("keydown", (event) => {
  if (!(event.ctrlKey || event.metaKey) || event.key !== "Enter") return;
  event.preventDefault();
  manualRun();
});
