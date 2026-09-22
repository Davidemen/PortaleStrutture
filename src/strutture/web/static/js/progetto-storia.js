// "Storia" disclosure (WORKBENCH_SPEC §14.3): every past revision of one element, each with its
// own data summary (revision number, date, sigla, nota) plus "Carica questa revisione" -- opens
// the tool with THOSE inputs loaded but NOT saved (a preview, no `elemento` in the resulting URL).
// Lazily fetched on first expand, same pattern as js/registro-row.js's own "Storia".
import { el, clear } from "./dom.js";
import { fetchRevisioni } from "./progetti-api.js";
import { stashAnteprima } from "./progetto-anteprima.js";
import { navigate } from "./router.js";

function formatDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" });
}

function metaText(revisione) {
  const parts = [`Revisione ${revisione.revisione}`, formatDate(revisione.data)];
  if (revisione.sigla) parts.push(revisione.sigla);
  if (revisione.nota) parts.push(revisione.nota);
  return parts.join(" · ");
}

export function buildProgettoStoria(elemento) {
  const body = el("div", { class: "ps-body" });
  const details = el("details", { class: "ps-details" }, [el("summary", { text: "Storia" }), body]);
  let loaded = false;

  details.addEventListener("toggle", () => {
    if (!details.open || loaded) return;
    loaded = true;
    body.textContent = "Caricamento…";
    fetchRevisioni(elemento.id)
      .then((revisioni) => {
        clear(body);
        if (revisioni.length === 0) {
          body.append(el("p", { class: "ps-empty", text: "Nessuna revisione precedente." }));
          return;
        }
        const list = el("ul", { class: "ps-list" });
        for (const revisione of [...revisioni].reverse()) {
          const loadBtn = el("button", {
            type: "button",
            class: "ps-load",
            text: "Carica questa revisione",
            onclick: () => {
              stashAnteprima(elemento.strumento, revisione.inputs);
              navigate(elemento.strumento, { anteprima: "1" });
            },
          });
          list.append(el("li", { class: "ps-item" }, [el("span", { class: "ps-item-meta", text: metaText(revisione) }), loadBtn]));
        }
        body.append(list);
      })
      .catch((error) => {
        clear(body);
        body.append(el("p", { class: "ps-empty", text: error.message || "Impossibile caricare la storia." }));
      });
  });

  return details;
}
