// Generic rail flyout dialog (WORKBENCH_SPEC.md #12): a single 280px panel, `position: fixed`
// and positioned purely in CSS (css/nav.css `.rail-flyout` -- header-bottom to window-bottom,
// flush against the collapsed rail) so it floats OVER the content and never shifts the grid.
// Non-modal `role="dialog"`: opens on click or Enter/Space/-> (never hover, callers wire that),
// closes on Esc, an outside click, a selection, or <-, and (only for Esc/<-) returns focus to the
// trigger. Content is supplied by the caller (js/tool-index.js owns what a category/Preferiti/
// Recenti flyout actually lists) -- this module only owns focus and the arrow-key/type-ahead
// roving navigation over the row buttons it is handed.
import { el, clear } from "./dom.js";

export function createFlyout() {
  let rows = [];
  let activeIndex = -1;
  let trigger = null;
  let onCloseCb = null;
  let currentBuildBody = null;

  const titleEl = el("h2", { class: "rail-flyout-title", id: "rail-flyout-title" });
  const body = el("div", { class: "rail-flyout-body" });
  const panel = el(
    "div",
    { class: "rail-flyout", role: "dialog", "aria-modal": "false", "aria-labelledby": "rail-flyout-title", hidden: true },
    [titleEl, body]
  );
  document.body.append(panel);

  function focusRow(index) {
    if (rows.length === 0) return;
    activeIndex = ((index % rows.length) + rows.length) % rows.length;
    rows[activeIndex].focus();
  }

  function detachGlobalListeners() {
    document.removeEventListener("keydown", onKeydown, true);
    document.removeEventListener("click", onDocClick, true);
  }

  function close({ restoreFocus = true } = {}) {
    if (panel.hidden) return;
    panel.hidden = true;
    detachGlobalListeners();
    const previousTrigger = trigger;
    trigger = null;
    currentBuildBody = null;
    if (restoreFocus && previousTrigger) previousTrigger.focus({ preventScroll: true });
    const cb = onCloseCb;
    onCloseCb = null;
    if (cb) cb();
  }

  function onDocClick(event) {
    if (panel.contains(event.target)) return;
    if (trigger && trigger.contains(event.target)) return;
    close({ restoreFocus: false });
  }

  function typeAhead(char) {
    const needle = char.toLowerCase();
    for (let step = 1; step <= rows.length; step++) {
      const index = (activeIndex + step) % rows.length;
      const title = (rows[index].dataset.title || "").toLowerCase();
      if (title.startsWith(needle)) {
        focusRow(index);
        return;
      }
    }
  }

  function onKeydown(event) {
    if (event.key === "Escape" || event.key === "ArrowLeft") {
      event.preventDefault();
      close();
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      focusRow(activeIndex + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      focusRow(activeIndex - 1);
    } else if (event.key.length === 1 && event.key.trim() && !event.ctrlKey && !event.metaKey && !event.altKey) {
      typeAhead(event.key);
    }
  }

  return {
    // `buildBody(bodyEl) -> HTMLButtonElement[]` appends the flyout's content into `bodyEl` and
    // returns the ordered "open" row buttons (each carrying `dataset.title`) for roving nav.
    open({ trigger: newTrigger, title, buildBody, onClose }) {
      const reopening = trigger === newTrigger && !panel.hidden;
      close({ restoreFocus: false });
      if (reopening) return; // a second activation of the same trigger just closes it
      trigger = newTrigger;
      onCloseCb = onClose || null;
      currentBuildBody = buildBody;
      titleEl.textContent = title;
      clear(body);
      rows = buildBody(body) || [];
      activeIndex = -1;
      // Review finding 23: position/size are pure CSS now (nav.css `.rail-flyout` -- fixed at the
      // collapsed rail's own width, header-bottom to window-bottom), not computed off the
      // trigger's on-screen position -- no measurement needed before showing it.
      panel.hidden = false;
      document.addEventListener("keydown", onKeydown, true);
      document.addEventListener("click", onDocClick, true);
      focusRow(0);
    },
    // Re-runs `buildBody` for the currently-open flyout without closing it (WORKBENCH_SPEC #12
    // "selection ... closes" is only about picking a TOOL -- toggling a (star) inside an open
    // Preferiti/Recenti flyout must update the list in place, not slam the dialog shut).
    refresh() {
      if (panel.hidden || !currentBuildBody) return;
      clear(body);
      rows = currentBuildBody(body) || [];
      if (activeIndex >= rows.length) activeIndex = rows.length - 1;
    },
    close,
    isOpen: () => !panel.hidden,
    activeTrigger: () => trigger,
  };
}
