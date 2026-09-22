// The 409 "conflitto di salvataggio" dialog for js/elemento-salva.js's "Salva"/"Salva come nuovo"
// (WORKBENCH_SPEC §14.1), split out purely to keep elemento-salva.js under the 400-line cap
// (§25.4: "if a further need arises... the 409-conflict dialog is split out first"). Takes every
// piece of caller state it needs to act (`getApi`, `save`+`requestRun` wiring done by the
// caller's own `applyReload`) rather than importing elemento-salva.js back, so there is no cycle.
import { el } from "./dom.js";
import { trapFocus } from "./nav-state.js";

// `{ attuale, applyReload(attuale), onSaveAsCopy() }` -> the mounted `<dialog>`. The caller owns
// `dialogEl`/`releaseTrap` bookkeeping (it already has a `closeDialog()`); this returns the node
// plus a `release` cleanup so the caller's own `closeDialog` can call both.
export function openConflictDialog({ attuale, applyReload, onSaveAsCopy, closeDialog }) {
  const titleId = "es-conflict-title";
  const dialogEl = el("dialog", { class: "es-dialog", role: "dialog", "aria-modal": "true", "aria-labelledby": titleId }, [
    el("h2", { id: titleId, text: "Conflitto di salvataggio" }),
    el("p", { text: "Modificato da un altro utente: ricarica e riprova." }),
    el("div", { class: "es-dialog-actions" }, [
      el("button", { type: "button", class: "es-dialog-save", text: "Ricarica", onclick: () => applyReload(attuale) }),
      el("button", { type: "button", class: "es-dialog-cancel", text: "Salva come copia", onclick: onSaveAsCopy }),
    ]),
  ]);
  document.body.append(dialogEl);
  dialogEl.addEventListener("close", closeDialog);
  const releaseTrap = trapFocus(dialogEl, { onEscape: closeDialog });
  dialogEl.showModal();
  return { dialogEl, releaseTrap };
}
