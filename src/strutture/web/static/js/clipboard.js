// Clipboard with a REAL fallback (bug fix, 2026-09-21): the app is reached over a VPN at
// http://<ip>:<port>, not a secure context, so `navigator.clipboard` is undefined there and the
// old call sites (forms-sections.js:copyShareLink, results-toolbar.js:wireValueCopy,
// table.js "Copia tabella") all showed "Copiato" unconditionally. `copyText()` never lies: it
// resolves true only when a copy really happened.
import { el } from "./dom.js";

function isMac() {
  return /Mac|iPhone|iPad|iPod/.test(navigator.platform || navigator.userAgent || "");
}

// Off-screen (not display:none -- execCommand("copy") requires the selection to be real)
// <textarea>, selected and copied via the legacy execCommand API, which still works on plain
// http. Restores whatever focus/selection existed before it ran.
function copyViaTextarea(text) {
  const previouslyFocused = document.activeElement;
  const textarea = el("textarea", { class: "sm-clip-offscreen", readonly: true, "aria-hidden": "true", tabindex: "-1", text });
  document.body.append(textarea);
  textarea.select();
  textarea.setSelectionRange(0, text.length);
  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch (error) {
    copied = false;
  }
  textarea.remove();
  if (previouslyFocused && typeof previouslyFocused.focus === "function") previouslyFocused.focus({ preventScroll: true });
  return copied;
}

// -> Promise<boolean>, true only when the text really reached the clipboard.
export async function copyText(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      // Not a secure context, permission denied, ... -- fall through to the textarea fallback.
    }
  }
  return copyViaTextarea(text);
}

// Shown wherever a copy attempt returns false: a small labelled read-only field holding the
// text, pre-selected, so the engineer can still copy it themselves (never silently claim
// success). `multiline` swaps the `<input>` for a `<textarea>` (table dumps can be long).
export function buildManualCopyField(text, label, { multiline = false } = {}) {
  const hint = isMac() ? "Copia non riuscita: premi ⌘C" : "Copia non riuscita: premi Ctrl+C";
  const inputId = `clip-fallback-${Math.random().toString(36).slice(2, 8)}`;
  const control = multiline
    ? el("textarea", { id: inputId, class: "sm-clip-fallback-input sm-clip-fallback-area", readonly: true, rows: "4", text })
    : el("input", { type: "text", id: inputId, class: "sm-clip-fallback-input", readonly: true, value: text });
  const field = el("span", { class: "sm-clip-fallback" }, [
    el("label", { for: inputId, class: "sm-clip-fallback-label", text: `${label} — ${hint}` }),
    control,
  ]);
  queueMicrotask(() => {
    control.focus();
    control.select();
  });
  return field;
}
