// Result tabs of an entry's parts -- WORKBENCH_SPEC §27.3 (optional part: [Copertura]
// [Accumulo]). A real `role="tablist"`: arrow keys (and Home/End) move the focus, Enter/Space
// (the button's own click) activates. The tab panel is the results sheet itself (#results-pane).
import { el, clear } from "./dom.js";

export function renderSchede(host, { parti, attiva, onScegli }) {
  clear(host);
  const bottoni = parti.map((parte) =>
    el("button", {
      type: "button",
      role: "tab",
      class: "vo-scheda",
      id: `voce-scheda-${parte.tool}`,
      "aria-selected": String(parte.tool === attiva),
      "aria-controls": "results-root",
      tabindex: parte.tool === attiva ? "0" : "-1",
      text: parte.titolo,
      onclick: () => onScegli(parte.tool),
    }),
  );
  const lista = el("div", { role: "tablist", class: "vo-schede-lista", "aria-label": "Parte mostrata nei risultati" }, bottoni);
  lista.addEventListener("keydown", (event) => {
    const indice = bottoni.indexOf(document.activeElement);
    if (indice < 0) return;
    const ultimo = bottoni.length - 1;
    const verso = { ArrowRight: indice + 1, ArrowLeft: indice - 1, Home: 0, End: ultimo }[event.key];
    if (verso === undefined) return;
    event.preventDefault();
    const prossimo = bottoni[(verso + bottoni.length) % bottoni.length];
    bottoni.forEach((bottone) => bottone.setAttribute("tabindex", bottone === prossimo ? "0" : "-1"));
    prossimo.focus();
  });
  host.append(lista);
}
