// #/progetti (WORKBENCH_SPEC §14.2): the project list -- ruled rows (codice, nome, committente,
// n. elementi, aggiornato), row actions Apri/Rinomina(inline)/Elimina(soft, confirm) plus a
// "Mostra eliminati" toggle revealing deleted rows with Ripristina; "Nuovo progetto" and "Importa"
// (.json) at the top. The shell renders this full-width, no Dati/Sintesi split (js/main.js
// `showProgettiList`).
import { el, clear } from "./dom.js";
import { fetchProgetti, createProgetto, updateProgetto, deleteProgetto, restoreProgetto, fetchElementi, importProgetto } from "./progetti-api.js";
import { navigate } from "./router.js";

function formatDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" });
}

function notifyProgettiChanged() {
  document.dispatchEvent(new CustomEvent("strutture:progetti-changed"));
}

export function renderProgettiList(root, { owner } = {}) {
  // This function itself never awaits before finishing its own skeleton (only its OWN inner
  // `load()` mutates a locally-owned `listHost` afterwards, never `root` directly) -- the owner
  // check only guards against TWO close-together list navigations resolving out of order (js/
  // progetto.js's own `renderProgetto` needs the same check after every `await` for the same
  // reason, see its comment for the full "cold import resolves slower" scenario).
  if (root._smOwner !== owner) return;
  clear(root);
  let progetti = [];
  let counts = new Map();
  let showDeleted = false;

  root.append(
    el("h2", { text: "Progetti" }),
    el("p", {
      class: "pj-intro",
      text: "Raggruppa gli elementi calcolati di una commessa: riaprili con i loro dati, vedi a colpo d'occhio quali sono verificati e stampa un'unica relazione per tutti.",
    }),
  );
  const errorHost = el("div", { class: "pj-error", role: "alert", hidden: true });
  const toolbar = el("div", { class: "pj-toolbar" });
  const newForm = el("form", { class: "pj-new-form" });
  newForm.hidden = true;
  const importStatus = el("p", { class: "pj-import-status", role: "status" });
  const listHost = el("div", { class: "pj-list-host" });
  root.append(errorHost, toolbar, newForm, importStatus, listHost);

  function setError(message) {
    errorHost.hidden = !message;
    errorHost.textContent = message || "";
  }

  // -- toolbar: Nuovo progetto / Importa / Mostra eliminati -----------------------------------------

  const newButton = el("button", {
    type: "button",
    class: "pj-new-btn",
    text: "Nuovo progetto",
    onclick: () => {
      newForm.hidden = !newForm.hidden;
      if (!newForm.hidden) newForm.querySelector("input").focus();
    },
  });
  const importInput = el("input", { type: "file", id: "pj-import-file", accept: ".json", class: "pj-import-file" });
  const importLabel = el("label", { class: "pj-import-btn", for: "pj-import-file", text: "Importa" });
  const showDeletedToggle = el("button", { type: "button", class: "pj-toggle-deleted", "aria-pressed": "false", text: "Mostra eliminati" });
  showDeletedToggle.addEventListener("click", () => {
    showDeleted = !showDeleted;
    showDeletedToggle.setAttribute("aria-pressed", String(showDeleted));
    load();
  });
  toolbar.append(newButton, importLabel, importInput, showDeletedToggle);

  const nomeInput = el("input", { type: "text", id: "pj-new-nome", required: true, maxlength: "120" });
  const codiceInput = el("input", { type: "text", id: "pj-new-codice", maxlength: "40" });
  const committenteInput = el("input", { type: "text", id: "pj-new-committente", maxlength: "120" });
  const newErrorEl = el("p", { class: "pj-new-error", role: "alert", hidden: true });
  newForm.append(
    el("div", { class: "pj-new-field" }, [el("label", { for: "pj-new-nome", text: "Nome" }), nomeInput]),
    el("div", { class: "pj-new-field" }, [el("label", { for: "pj-new-codice", text: "Codice" }), codiceInput]),
    el("div", { class: "pj-new-field" }, [el("label", { for: "pj-new-committente", text: "Committente" }), committenteInput]),
    newErrorEl,
    el("div", { class: "pj-new-actions" }, [
      el("button", { type: "submit", class: "pj-new-save", text: "Crea progetto" }),
      el("button", { type: "button", class: "pj-new-cancel", text: "Annulla", onclick: () => { newForm.hidden = true; } }),
    ]),
  );
  newForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const nome = nomeInput.value.trim();
    if (!nome) {
      newErrorEl.textContent = "Il nome è obbligatorio.";
      newErrorEl.hidden = false;
      return;
    }
    createProgetto({ codice: codiceInput.value.trim(), nome, committente: committenteInput.value.trim() })
      .then((created) => {
        notifyProgettiChanged();
        navigate(`progetti/${created.id}`);
      })
      .catch((error) => {
        newErrorEl.textContent = error.message || "Impossibile creare il progetto.";
        newErrorEl.hidden = false;
      });
  });

  importInput.addEventListener("change", () => {
    const file = importInput.files && importInput.files[0];
    if (!file) return;
    importStatus.textContent = "Importazione…";
    file
      .text()
      .then((text) => {
        let payload;
        try {
          payload = JSON.parse(text);
        } catch (error) {
          throw new Error("Il file non è un JSON valido.");
        }
        return importProgetto(payload);
      })
      .then(({ progetto, avvisi }) => {
        progetti = [progetto, ...progetti];
        notifyProgettiChanged();
        renderList();
        importStatus.textContent =
          avvisi.length > 0
            ? `Importato "${progetto.nome}" con ${avvisi.length} avviso${avvisi.length === 1 ? "" : "i"}: ${avvisi.join("; ")}`
            : `Importato "${progetto.nome}".`;
      })
      .catch((error) => {
        importStatus.textContent = error.message || "Impossibile importare il progetto.";
      })
      .finally(() => {
        importInput.value = "";
      });
  });

  // -- row actions ---------------------------------------------------------------------------------

  function buildRenameForm(progetto, actionsHost, nomeCell) {
    clear(actionsHost);
    const input = el("input", { type: "text", class: "pj-rename-input", value: progetto.nome, maxlength: "120", required: true });
    const errorEl = el("p", { class: "pj-inline-error", role: "alert", hidden: true });
    clear(nomeCell);
    nomeCell.append(input, errorEl);
    input.focus();
    input.select();
    const saveBtn = el("button", {
      type: "button",
      class: "pj-action",
      text: "Salva",
      onclick: async () => {
        const nome = input.value.trim();
        if (!nome) {
          errorEl.textContent = "Il nome è obbligatorio.";
          errorEl.hidden = false;
          return;
        }
        saveBtn.disabled = true;
        try {
          const result = await updateProgetto(progetto.id, { codice: progetto.codice, nome, committente: progetto.committente, note: progetto.note, revisione: progetto.revisione });
          if (result.conflict) {
            errorEl.textContent = result.message || "Modificato da un altro utente: ricarica e riprova.";
            errorEl.hidden = false;
            saveBtn.disabled = false;
            return;
          }
          progetti = progetti.map((item) => (item.id === progetto.id ? result.data : item));
          notifyProgettiChanged();
          renderList();
        } catch (error) {
          errorEl.textContent = error.message || "Impossibile rinominare.";
          errorEl.hidden = false;
          saveBtn.disabled = false;
        }
      },
    });
    actionsHost.append(saveBtn, el("button", { type: "button", class: "pj-action", text: "Annulla", onclick: renderList }));
  }

  function buildDeleteConfirm(progetto, actionsHost) {
    clear(actionsHost);
    const errorEl = el("p", { class: "pj-inline-error", role: "alert", hidden: true });
    const confirmBtn = el("button", {
      type: "button",
      class: "pj-action pj-action--danger",
      text: "Conferma eliminazione",
      onclick: async () => {
        confirmBtn.disabled = true;
        try {
          const result = await deleteProgetto(progetto.id, progetto.revisione);
          if (result.conflict) {
            errorEl.textContent = result.message || "Modificato da un altro utente: ricarica e riprova.";
            errorEl.hidden = false;
            confirmBtn.disabled = false;
            return;
          }
          notifyProgettiChanged();
          load();
        } catch (error) {
          errorEl.textContent = error.message || "Impossibile eliminare.";
          errorEl.hidden = false;
          confirmBtn.disabled = false;
        }
      },
    });
    actionsHost.append(el("span", { class: "pj-inline-question", text: "Confermi l'eliminazione?" }), confirmBtn, el("button", { type: "button", class: "pj-action", text: "Annulla", onclick: renderList }), errorEl);
  }

  function buildActions(progetto, actionsHost, nomeCell) {
    clear(actionsHost);
    if (progetto.eliminato) {
      actionsHost.append(
        el("button", {
          type: "button",
          class: "pj-action",
          text: "Ripristina",
          onclick: async () => {
            try {
              await restoreProgetto(progetto.id);
              notifyProgettiChanged();
              load();
            } catch (error) {
              setError(error.message || "Impossibile ripristinare.");
            }
          },
        }),
      );
      return;
    }
    actionsHost.append(
      el("a", { class: "pj-action", href: `#/progetti/${progetto.id}`, text: "Apri" }),
      el("button", { type: "button", class: "pj-action", text: "Rinomina", onclick: () => buildRenameForm(progetto, actionsHost, nomeCell) }),
      el("button", { type: "button", class: "pj-action", text: "Elimina", onclick: () => buildDeleteConfirm(progetto, actionsHost) }),
    );
  }

  function buildRow(progetto) {
    const isDeleted = Boolean(progetto.eliminato);
    const row = el("li", { class: `pj-row${isDeleted ? " pj-row--deleted" : ""}`, "data-id": progetto.id });
    const nomeCell = el("span", { class: "pj-row-nome" }, [el("a", { href: `#/progetti/${progetto.id}`, text: progetto.nome })]);
    const grid = el("div", { class: "pj-row-grid" }, [
      el("span", { class: "pj-row-codice", text: progetto.codice || "—" }),
      nomeCell,
      el("span", { class: "pj-row-committente", text: progetto.committente || "—" }),
      el("span", { class: "pj-row-count", text: counts.has(progetto.id) ? String(counts.get(progetto.id)) : "…" }),
      el("span", { class: "pj-row-updated", text: formatDate(progetto.aggiornato) }),
    ]);
    const actionsHost = el("div", { class: "pj-row-actions" });
    buildActions(progetto, actionsHost, nomeCell);
    row.append(grid, actionsHost);
    return row;
  }

  function visibleProgetti() {
    return showDeleted ? progetti.filter((p) => p.eliminato) : progetti.filter((p) => !p.eliminato);
  }

  function renderList() {
    clear(listHost);
    const visible = visibleProgetti();
    if (visible.length === 0) {
      listHost.append(
        showDeleted
          ? el("p", { class: "pj-empty", text: "Nessun progetto eliminato." })
          : el("p", { class: "pj-empty", text: "Nessun progetto ancora. Crea il primo con «Nuovo progetto»." }),
      );
      return;
    }
    const list = el("ul", { class: "pj-list" });
    for (const progetto of visible) list.append(buildRow(progetto));
    listHost.append(list);
  }

  // Patches each row's own "n. elementi" cell IN PLACE rather than calling `renderList()` again:
  // a full rebuild here would blow away whatever the engineer is CURRENTLY mid-edit on (the
  // "Rinomina" inline form, a "Conferma eliminazione" prompt) the instant this slower, per-project
  // fetch happens to land -- same "update in place, never rebuild what is mid-edit" rule as
  // js/registro-row.js's own sign-off form. `generation` still guards it (a stale count is
  // harmless -- the row it patches is keyed by id, not position -- but skipping it once a NEWER
  // `load()` has already started keeps this from ever fighting that one over the DOM).
  function loadCounts(generation) {
    Promise.all(visibleProgetti().map((progetto) => fetchElementi(progetto.id).then((list) => [progetto.id, list.length]).catch(() => [progetto.id, null])))
      .then((pairs) => {
        if (generation !== loadGeneration) return;
        counts = new Map(pairs);
        for (const [id, count] of counts) {
          if (count === null) continue;
          const cell = listHost.querySelector(`.pj-row[data-id="${CSS.escape(id)}"] .pj-row-count`);
          if (cell) cell.textContent = String(count);
        }
      })
      .catch(() => {
        /* row counts degrade to "…" only -- opening the project still shows the real elements */
      });
  }

  // `generation` (bumped on every call) makes sure only the LATEST `load()` -- not necessarily
  // the latest to actually RESOLVE -- ever applies its result: "Elimina" then immediately
  // "Ripristina" (or the reverse) fire two independent fetches whose responses can arrive out of
  // order, and without this a stale, already-superseded one could overwrite the correct one.
  let loadGeneration = 0;

  function load() {
    setError(null);
    const generation = ++loadGeneration;
    fetchProgetti({ inclusiEliminati: true })
      .then((list) => {
        if (generation !== loadGeneration) return;
        progetti = list;
        renderList();
        loadCounts(generation);
      })
      .catch((error) => {
        if (generation !== loadGeneration) return;
        setError(error.message || "Impossibile caricare l'elenco dei progetti.");
      });
  }

  load();
}
