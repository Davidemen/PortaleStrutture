// The MIDAS personal API key: sessionStorage ONLY (MIDAS.md §2 rule 2) -- never localStorage,
// never appended to the URL/share link, never logged. Cleared when the tab closes, which is the
// point: the key is a per-engineer secret, not app state worth persisting across sessions.
// Deliberately does not reuse storage.js (that module is explicitly localStorage, see its own
// header comment) so a future edit there can never accidentally leak the key.
const KEY_NAME = "midas.key";

export function getMidasKey() {
  try {
    return window.sessionStorage.getItem(KEY_NAME) || "";
  } catch (error) {
    return ""; // storage unavailable (private mode, quota): fall back to "no key typed"
  }
}

export function setMidasKey(value) {
  try {
    if (value) window.sessionStorage.setItem(KEY_NAME, value);
    else window.sessionStorage.removeItem(KEY_NAME);
    return true;
  } catch (error) {
    return false;
  }
}

export function clearMidasKey() {
  try {
    window.sessionStorage.removeItem(KEY_NAME);
  } catch (error) {
    // best-effort: nothing to recover from a storage failure on removal
  }
}
