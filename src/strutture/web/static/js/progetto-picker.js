// Header project picker (WORKBENCH_SPEC §14.1): a <select> "Progetto: <nome>" listing active
// projects plus "Nessun progetto" and "Nuovo progetto..." (inline mini-form: codice, nome,
// committente). The choice is kept per browser (localStorage) -- "nothing else in the app changes
// when no project is selected". `getCurrentProgetto`/`setCurrentProgetto` are the ONE owner of
// that storage key: js/elemento-salva.js reads/writes the current project through them too (never
// the raw key), so its own tool-page widget and this header select always agree, and
// `strutture:progetto-changed` is how each side learns the other one just changed it.
import { el, clear } from "./dom.js";
import { readJSON, writeJSON } from "./storage.js";
import { fetchProgetti, createProgetto } from "./progetti-api.js";

const CURRENT_KEY = "sm.progetto.corrente"; // {id, nome} | null
const NEW_VALUE = "__nuovo__";

export function getCurrentProgetto() {
  return readJSON(CURRENT_KEY, null);
}

export function setCurrentProgetto(progetto) {
  const value = progetto ? { id: progetto.id, nome: progetto.nome } : null;
  writeJSON(CURRENT_KEY, value);
  document.dispatchEvent(new CustomEvent("strutture:progetto-changed", { detail: value }));
  return value;
}

function optionLabel(progetto) {
  return progetto.codice ? `${progetto.codice} — ${progetto.nome}` : progetto.nome;
}

export function initProgettoPicker(root) {
  if (!root) return;
  let progetti = [];

  const select = el("select", { id: "progetto-picker-select", class: "pp-select", "aria-label": "Progetto corrente" });
  const formHost = el("div", { class: "pp-new-form" });
  formHost.hidden = true;
  root.append(el("label", { class: "pp-label", for: "progetto-picker-select", text: "Progetto" }), select, formHost);

  function renderOptions() {
    clear(select);
    const current = getCurrentProgetto();
    select.append(el("option", { value: "", text: "Nessun progetto", selected: !current }));
    for (const progetto of progetti) {
      select.append(el("option", { value: progetto.id, text: optionLabel(progetto), selected: Boolean(current && current.id === progetto.id) }));
    }
    select.append(el("option", { value: NEW_VALUE, text: "Nuovo progetto…" }));
  }

  function closeNewForm() {
    formHost.hidden = true;
    clear(formHost);
  }

  function openNewForm() {
    clear(formHost);
    const nomeInput = el("input", { type: "text", id: "pp-new-nome", required: true, maxlength: "120" });
    const codiceInput = el("input", { type: "text", id: "pp-new-codice", maxlength: "40" });
    const committenteInput = el("input", { type: "text", id: "pp-new-committente", maxlength: "120" });
    const errorEl = el("p", { class: "pp-new-error", role: "alert", hidden: true });
    const form = el("form", { class: "pp-new-fields" }, [
      el("div", { class: "pp-new-field" }, [el("label", { for: "pp-new-nome", text: "Nome" }), nomeInput]),
      el("div", { class: "pp-new-field" }, [el("label", { for: "pp-new-codice", text: "Codice" }), codiceInput]),
      el("div", { class: "pp-new-field" }, [el("label", { for: "pp-new-committente", text: "Committente" }), committenteInput]),
      errorEl,
      el("div", { class: "pp-new-actions" }, [
        el("button", { type: "submit", class: "pp-new-save", text: "Crea progetto" }),
        el("button", {
          type: "button",
          class: "pp-new-cancel",
          text: "Annulla",
          onclick: () => {
            closeNewForm();
            renderOptions();
          },
        }),
      ]),
    ]);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const nome = nomeInput.value.trim();
      if (!nome) {
        errorEl.textContent = "Il nome è obbligatorio.";
        errorEl.hidden = false;
        return;
      }
      createProgetto({ codice: codiceInput.value.trim(), nome, committente: committenteInput.value.trim() })
        .then((created) => {
          progetti = [...progetti, created];
          setCurrentProgetto(created);
          closeNewForm();
          renderOptions();
        })
        .catch((error) => {
          errorEl.textContent = error.message || "Impossibile creare il progetto.";
          errorEl.hidden = false;
        });
    });
    formHost.append(form);
    formHost.hidden = false;
    nomeInput.focus();
  }

  select.addEventListener("change", () => {
    if (select.value === NEW_VALUE) {
      openNewForm();
      return;
    }
    closeNewForm();
    const chosen = progetti.find((progetto) => progetto.id === select.value);
    setCurrentProgetto(chosen || null);
  });

  function load() {
    fetchProgetti()
      .then((list) => {
        progetti = list;
        renderOptions();
      })
      .catch(() => {
        // the header select degrades to "Nessun progetto" only -- the #/progetti pages themselves
        // still show the real fetch error to someone who actually opens them
      });
  }

  // Another part of the app changed the current project (js/elemento-salva.js opening an element
  // deep link, or its own "Salva in progetto" dialog creating a project) -- reflect it here too.
  document.addEventListener("strutture:progetto-changed", () => renderOptions());
  // A project was created/renamed/deleted elsewhere (list/detail pages) -- refetch the option list.
  document.addEventListener("strutture:progetti-changed", load);

  load();
}
