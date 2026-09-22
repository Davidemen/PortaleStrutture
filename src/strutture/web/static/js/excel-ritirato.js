// Excel mode retires per approved tool (WORKBENCH_SPEC §16). A tool is "approvato" once every
// register entry it has is decided, none pending and none rejected (js/registro-stato.js's own
// `isApproved`, sharing the SAME cached riepilogo the per-tool registro indicator already fetches).
// For such a tool the `legacy_compat` input ("Riproduci il foglio Excel originale") is hidden in
// Dati (value forced false), the Avanzate fold hides too once it has nothing else left in it, and
// "Confronta con Excel" is gated off separately, at render time, by js/results.js. Mounted directly
// by js/forms.js's `renderForm` (a plain function call, exactly like js/elemento-salva.js/js/
// provenienza.js) -- js/registro-stato.js's own cache is prefetched at boot (js/main.js, fire-and-
// forget), but that prefetch can still be in flight the first time a tool page mounts, so this
// re-applies once it resolves too (same fallback js/registro-indicator.js already uses for its own
// header link) rather than only reacting to a LATER sign-off.
import { el } from "./dom.js";
import { isApproved, getRiepilogo, ensureRiepilogo } from "./registro-stato.js";

const FIELD_NAME = "legacy_compat";
const NOTE_TEXT =
  "Modalità Excel non più disponibile: tutte le correzioni di questo strumento sono state approvate.";

let mounted = null; // {toolForm, tool, note} | null -- the currently mounted tool page, if any

function advancedIsEmpty(toolForm) {
  const details = toolForm.querySelector(".f-advanced");
  if (!details) return true;
  return details.querySelectorAll(".f-field:not([hidden])").length === 0;
}

// Returns whether it actually had to flip a checked box off (only THAT case earns the dismissible
// note -- a tool whose switch was already off has nothing new to explain).
function forceOff(toolForm, { live }) {
  const input = toolForm.elements.namedItem(FIELD_NAME);
  if (!input || !input.checked) return false;
  input.checked = false;
  // Only a LIVE transition (the tool just became approved while its page is already open, WORKBENCH_
  // SPEC §16 "without a reload") is a real value change needing re-validation/re-run -- the very
  // first, synchronous mount pass (share link/saved element carrying `legacy_compat: true`) runs
  // BEFORE forms.js's own initial `sectionsApi.refresh()`/`updateRunUi()` read the DOM, so setting
  // `.checked` here is enough; nothing has read the stale `true` value yet to need correcting.
  if (live) input.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
}

function buildNote() {
  const note = el("p", { class: "xr-note" });
  note.hidden = true;
  note.append(
    el("span", { text: `${NOTE_TEXT} ` }),
    el("button", { type: "button", class: "xr-note-close", text: "Chiudi", onclick: () => { note.hidden = true; } }),
  );
  return note;
}

function apply(ctx, { live }) {
  const { toolForm, tool, note } = ctx;
  const wrapper = toolForm.querySelector(`.f-field[data-field="${FIELD_NAME}"]`);
  if (!wrapper) return; // this tool's schema has no legacy_compat field -- nothing to retire
  const details = toolForm.querySelector(".f-advanced");
  if (isApproved(tool)) {
    const forced = forceOff(toolForm, { live });
    wrapper.hidden = true;
    if (details) details.hidden = advancedIsEmpty(toolForm);
    if (forced) note.hidden = false;
  } else {
    wrapper.hidden = false;
    if (details) details.hidden = false;
  }
}

// `tool` is the tool NAME (registro-stato.js's `isApproved` keys the riepilogo by it). Returns the
// dismissible note element for forms.js to place under the tool title, next to js/provenienza.js's
// own note.
export function mountExcelRitirato({ toolForm, tool }) {
  const note = buildNote();
  mounted = { toolForm, tool, note };
  apply(mounted, { live: false });
  if (!getRiepilogo()) {
    // The boot-time prefetch was still in flight at the moment above -- `isApproved` had nothing
    // to answer with, so the pass just ran treated this tool as not-yet-approved. Re-apply once the
    // fetch actually resolves; `live: true` because, unlike the pass above, real time may have
    // passed (a live run could already have fired with a stale value) -- `mounted === ctx` drops
    // this if a faster tool switch already replaced it with a different page in the meantime.
    const ctx = mounted;
    ensureRiepilogo()
      .then(() => {
        if (mounted === ctx) apply(ctx, { live: true });
      })
      .catch(() => {});
  }
  return note;
}

// One listener for the module's whole lifetime (not re-added per mount, so switching tools never
// leaks one): only ever acts on whichever tool is CURRENTLY mounted.
document.addEventListener("strutture:registro-stato-changed", () => {
  if (mounted) apply(mounted, { live: true });
});
