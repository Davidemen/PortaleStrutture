// The optimistic-locking 409 dialog ("Ricarica"/"Salva come copia"), extracted out of
// js/elemento-salva.js (WORKBENCH_SPEC §19.5: "373 lines today, so both callers share it") --
// js/elemento-salva.js's own PUT and js/varianti-tieni.js's §19.4 "Aggiorna" both hit the same
// `PUT /api/elementi/{id}` 409 shape and need the identical two-way choice.
import { el } from "./dom.js";
import { trapFocus } from "./nav-state.js";

// `onRicarica(attuale)`/`onSalvaCopia()` are called AFTER the dialog is closed -- neither caller
// needs to close it itself. Returns nothing: the dialog owns its own lifecycle end to end.
export function apriConflittoDialog({ attuale, onRicarica, onSalvaCopia }) {
  const titleId = "ec-conflict-title";
  let dialogEl = null;
  let releaseTrap = null;

  function close() {
    if (releaseTrap) {
      releaseTrap();
      releaseTrap = null;
    }
    if (dialogEl) {
      const node = dialogEl;
      dialogEl = null;
      node.close();
      node.remove();
    }
  }

  dialogEl = el("dialog", { class: "es-dialog", role: "dialog", "aria-modal": "true", "aria-labelledby": titleId }, [
    el("h2", { id: titleId, text: "Conflitto di salvataggio" }),
    el("p", { text: "Modificato da un altro utente: ricarica e riprova." }),
    el("div", { class: "es-dialog-actions" }, [
      el("button", {
        type: "button",
        class: "es-dialog-save",
        text: "Ricarica",
        onclick: () => {
          close();
          onRicarica(attuale);
        },
      }),
      el("button", {
        type: "button",
        class: "es-dialog-cancel",
        text: "Salva come copia",
        onclick: () => {
          close();
          onSalvaCopia();
        },
      }),
    ]),
  ]);
  document.body.append(dialogEl);
  dialogEl.addEventListener("close", close);
  releaseTrap = trapFocus(dialogEl, { onEscape: close });
  dialogEl.showModal();
}
