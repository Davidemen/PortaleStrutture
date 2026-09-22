// Shared cache for `GET /api/divergences/riepilogo` (WORKBENCH_SPEC §13.2/§16). Both
// js/registro-indicator.js's own per-tool link/banner AND the Excel-mode retirement logic
// (js/excel-ritirato.js's hidden switch/note, js/results.js's `canCompare` gate) need the SAME
// data, refreshed on the SAME event -- fetched here ONCE and cached, never duplicated per
// consumer. `js/main.js` calls `ensureRiepilogo()` at boot (alongside `fetchTools()`) so the data
// is already synchronously available by the time the FIRST `strutture:tool-schema` fires -- the
// same "prefetch once, read synchronously forever after" contract js/main.js already gives the
// `tools` list itself, needed here so an already-approved tool never flashes its retired controls
// on the very first paint (an on-demand fetch, only starting once a tool page is reached, could
// still be in flight when that first render happens).
import { fetchRiepilogo } from "./registro-api.js";

let cache = null; // `{[tool]: {da_confermare, approvato, respinto}}` | null (not loaded, or load failed)
let pending = null; // in-flight Promise<...> | null -- de-dupes concurrent callers

function load() {
  if (cache) return Promise.resolve(cache);
  if (pending) return pending;
  pending = fetchRiepilogo()
    .then((body) => {
      cache = body;
      pending = null;
      return cache;
    })
    .catch((error) => {
      pending = null;
      throw error;
    });
  return pending;
}

// Synchronous read: `null` before the first successful load. Callers that can tolerate a later
// re-render (registro-indicator.js) treat that as "render nothing yet"; callers that need a
// same-render answer (results.js's `canCompare`) rely on `ensureRiepilogo()` having already been
// awaited at boot instead.
export function getRiepilogo() {
  return cache;
}

export function ensureRiepilogo() {
  return load();
}

// WORKBENCH_SPEC §16: "approvato" needs register entries AND both counts at zero -- a tool with NO
// entries at all (`counts` undefined) is not "approved", it simply has nothing to confirm yet, and
// the Excel switch stays exactly as available as it is today.
export function isApproved(toolName, riepilogo = cache) {
  const counts = riepilogo && riepilogo[toolName];
  if (!counts) return false;
  return counts.da_confermare === 0 && counts.respinto === 0 && (counts.approvato || 0) > 0;
}

// Re-fetches after any sign-off (registro.js dispatches this on a successful save/bulk-save) and
// tells every consumer once the fresh data has landed, so a tool page left open in the same
// session can react without a reload (WORKBENCH_SPEC §16: "the switch and the compare button come
// back without a reload").
document.addEventListener("strutture:registro-changed", () => {
  cache = null;
  pending = null;
  load()
    .catch(() => {})
    .then(() => document.dispatchEvent(new CustomEvent("strutture:registro-stato-changed")));
});
