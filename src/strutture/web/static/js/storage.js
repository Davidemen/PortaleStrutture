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
