// "comune alla voce" chip next to the label of a common field -- WORKBENCH_SPEC §27.4. A small
// disclosure (keyboard reachable, CSP-safe `<details>`) holding the "Stacca" / "Ricollega" text
// button. Pure DOM decoration: the caller decides what the buttons do.
import { el } from "./dom.js";
import { condiviso } from "./voce-comuni.js";

export function decoraComuni(form, { voce, staccati, prefisso = "", onStacca, onRicollega }) {
  form.querySelectorAll(".vo-comune").forEach((chip) => chip.remove());
  for (const campo of voce.comuni) {
    const wrapper = form.querySelector(`.f-field[data-field="${prefisso}${campo}"]`);
    if (!wrapper) continue;
    const comune = condiviso(voce, staccati, campo);
    const azione = el("button", {
      type: "button",
      class: "vo-comune-azione",
      text: comune ? "Stacca" : "Ricollega",
      title: comune
        ? "Da qui in avanti questa parte usa un valore suo"
        : "Torna a usare il valore comune della voce",
      onclick: () => (comune ? onStacca(campo) : onRicollega(campo)),
    });
    const chip = el("details", { class: comune ? "vo-comune" : "vo-comune vo-comune--staccato" }, [
      el("summary", { class: "vo-comune-etichetta" }, [
        el("span", { class: "vo-comune-icona", "aria-hidden": "true", text: comune ? "⇄" : "↛" }),
        comune ? " comune alla voce" : " staccato",
      ]),
      azione,
    ]);
    const host = wrapper.querySelector(".f-field-labelcell") || wrapper;
    host.append(chip);
  }
}
