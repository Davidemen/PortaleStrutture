// The "Carica questa revisione" hand-off (WORKBENCH_SPEC §14.3): js/progetto-storia.js stashes a
// past revision's inputs here before navigating to `#/<tool>?anteprima=1`; js/elemento-salva.js
// reads (and clears) it on that route to fill the form WITHOUT saving anything. sessionStorage,
// not localStorage -- a one-shot hand-off that should never survive a closed tab the way persisted
// inputs do. Split out from both callers (rather than owned by either) purely to keep each of
// those two files under the spec's own 400-line cap.
const KEY = "sm.progetto.anteprima";

export function stashAnteprima(tool, inputs) {
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify({ tool, inputs }));
  } catch (error) {
    // best-effort: a storage failure just means the preview opens with the tool's own normal
    // (saved/default) inputs instead of the requested revision -- never a hard navigation failure
  }
}

export function takeAnteprimaStash(tool) {
  let raw = null;
  try {
    raw = window.sessionStorage.getItem(KEY);
    window.sessionStorage.removeItem(KEY);
  } catch (error) {
    return null;
  }
  if (!raw) return null;
  try {
    const stash = JSON.parse(raw);
    return stash && stash.tool === tool ? stash : null;
  } catch (error) {
    return null;
  }
}
