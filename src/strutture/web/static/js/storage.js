// localStorage wrapper -- never throws (quota/parse failures fall back to
// the caller's default). Namespace "sm.": sm.inputs.<tool>, sm.cartiglio,
// sm.ui.openGroups, sm.ui.pane.

export function readJSON(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    if (raw === null) return fallback;
    return JSON.parse(raw);
  } catch (error) {
    return fallback;
  }
}

export function writeJSON(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    return false;
  }
}

export function remove(key) {
  try {
    window.localStorage.removeItem(key);
  } catch (error) {
    // best-effort: nothing to recover from a storage failure on removal
  }
}

// Same never-throws contract as the localStorage helpers above, backed by sessionStorage instead
// -- WORKBENCH_SPEC §19.1: the varianti working set ("sm.varianti.<tool>") must survive a reload
// but die with the tab, which is exactly sessionStorage's own lifetime, unlike localStorage above.
export function readSessionJSON(key, fallback) {
  try {
    const raw = window.sessionStorage.getItem(key);
    if (raw === null) return fallback;
    return JSON.parse(raw);
  } catch (error) {
    return fallback;
  }
}

export function writeSessionJSON(key, value) {
  try {
    window.sessionStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    return false;
  }
}

export function removeSession(key) {
  try {
    window.sessionStorage.removeItem(key);
  } catch (error) {
    // best-effort: nothing to recover from a storage failure on removal
  }
}
