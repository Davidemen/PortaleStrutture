// WORKBENCH_SPEC §19.2: opening an element (`?elemento=`), a `?anteprima=1` revision preview, or a
// "Usa in..." arrival (`?da=`) while a varianti set (js/varianti-bar.js) is still open must never
// silently overwrite the active variant's inputs -- each of those three loaders calls
// `confermaChiusuraVarianti(tool)` BEFORE touching the form and only proceeds if it resolves true.
// Extracted so js/elemento-salva.js and js/provenienza.js share one dialog instead of two copies.
import { el } from "./dom.js";
import { trapFocus } from "./nav-state.js";
import { chiudiVarianti } from "./varianti-state.js";
import { setHistoryScope } from "./annulla-ui.js";

// Resolves `true` ("Chiudi e carica": the set is discarded, caller applies its data) or `false`
// ("Annulla": caller must not apply anything, e.g. by returning early without further side effects).
export function confermaChiusuraVarianti(tool) {
  return new Promise((resolve) => {
    const titleId = "vc-confirm-title";
    let dialogEl = null;
    let releaseTrap = null;

    function close(result) {
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
      resolve(result);
    }

    dialogEl = el("dialog", { class: "es-dialog", role: "dialog", "aria-modal": "true", "aria-labelledby": titleId }, [
      el("h2", { id: titleId, text: "Chiudere le varianti aperte?" }),
      el("p", { text: "Caricare questi dati chiude le varianti aperte: quelle non salvate come elemento vanno perse." }),
      el("div", { class: "es-dialog-actions" }, [
        el("button", {
          type: "button",
          class: "es-dialog-save",
          text: "Chiudi e carica",
          onclick: () => {
            chiudiVarianti(tool);
            setHistoryScope(tool);
            // A hash-only route change (`?elemento=`/`?anteprima=1`/`?da=`) never remounts
            // js/varianti-bar.js on its own -- tell whichever instance is mounted to drop its
            // own in-memory set too, or the strip would keep showing the just-closed variants.
            document.dispatchEvent(new CustomEvent("strutture:varianti-chiuse", { detail: { tool } }));
            close(true);
          },
        }),
        el("button", {
          type: "button",
          class: "es-dialog-cancel",
          text: "Annulla",
          onclick: () => close(false),
        }),
      ]),
    ]);
    document.body.append(dialogEl);
    dialogEl.addEventListener("close", () => close(false));
    releaseTrap = trapFocus(dialogEl, { onEscape: () => close(false) });
    dialogEl.showModal();
  });
}
