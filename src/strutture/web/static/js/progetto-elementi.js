// The element list of a project page (WORKBENCH_SPEC §14.3): ruled rows (sigla chip, nome, stato
// icon+word, eta max, verifica governante, aggiornato), row actions Apri/Duplica/Rinomina/Storia/
// Elimina, sort by aggiornato desc, filter by tool. `Rinomina` PUTs the FULL element record (the
// server has no rename-only endpoint -- `_ElementoUpdateBody.inputs` defaults to `{}`, so a PUT
// that omitted it would silently WIPE the element's saved inputs) -- `elemento.inputs`/`sintesi`/
// etc. are already on hand from the list response itself, never re-fetched.
//
// API gap (reported, not worked around): WORKBENCH_SPEC §14.3 asks for "Elimina / Ripristina" on
// every element row, but `ProjectRepository`/`InMemoryProjectRepository`
// (src/strutture/storage/progetti_memory.py) have no `ripristina_elemento`, no route exists for
// one, and `list_elementi` never returns soft-deleted elements at all (unlike `list_progetti`,
// which takes `inclusi_eliminati`) -- there is no way to even SEE a deleted element again, let
// alone restore it. "Elimina" (soft delete, via the existing DELETE endpoint) is implemented;
// "Ripristina" is not, since shipping a button with no working endpoint behind it would be worse
// than omitting it.
import { el, clear } from "./dom.js";
import { fetchTools } from "./api.js";
import { fetchElementi, deleteElemento, duplicateElemento, updateElemento } from "./progetti-api.js";
import { siglaChip } from "./nav-state.js";
import { formatUtilisation } from "./format.js";
import { buildProgettoStoria } from "./progetto-storia.js";

// Exported: js/progetto-relazione.js's per-element sub-cartiglio ("stato") reuses the SAME words.
export const STATO_LABELS = { verificato: "✓ Verificato", non_verificato: "✕ Non verificato", dati_modificati: "○ Dati modificati" };

function formatDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" });
}

function etaMaxText(elemento) {
  const value = elemento.sintesi && typeof elemento.sintesi.eta_max === "number" ? elemento.sintesi.eta_max : null;
  return value === null ? "—" : formatUtilisation(value);
}

export function renderProgettoElementi(root, { progetto, params = {} } = {}) {
  clear(root);
  let elementi = [];
  let toolsByName = new Map();
  let filterStrumento = params.strumento || "";

  root.append(el("h3", { text: "Elementi" }));
  const errorHost = el("div", { class: "pe-error", role: "alert", hidden: true });
  const toolbar = el("div", { class: "pe-toolbar" });
  const filterSelect = el("select", { id: "pe-filter-strumento", class: "pe-filter-select" });
  toolbar.append(el("label", { class: "pe-filter-label", for: "pe-filter-strumento", text: "Strumento" }), filterSelect);
  const listHost = el("div", { class: "pe-list-host" });
  root.append(errorHost, toolbar, listHost);

  function setError(message) {
    errorHost.hidden = !message;
    errorHost.textContent = message || "";
  }

  function visibleElementi() {
    const list = filterStrumento ? elementi.filter((item) => item.strumento === filterStrumento) : elementi;
    return [...list].sort((a, b) => (b.aggiornato || "").localeCompare(a.aggiornato || ""));
  }

  function buildFilterOptions() {
    clear(filterSelect);
    filterSelect.append(el("option", { value: "", text: "Tutti gli strumenti" }));
    const seen = new Map();
    for (const item of elementi) {
      if (seen.has(item.strumento)) continue;
      const tool = toolsByName.get(item.strumento);
      seen.set(item.strumento, tool ? `${tool.sigla} — ${tool.title}` : `${item.strumento} (non disponibile)`);
    }
    for (const [name, label] of seen) filterSelect.append(el("option", { value: name, text: label, selected: name === filterStrumento }));
  }

  function replaceElemento(next) {
    elementi = elementi.map((item) => (item.id === next.id ? next : item));
  }

  function removeElemento(id) {
    elementi = elementi.filter((item) => item.id !== id);
  }

  // -- row actions ---------------------------------------------------------------------------------

  function buildRenameForm(elemento, actionsHost) {
    clear(actionsHost);
    const input = el("input", { type: "text", class: "pe-rename-input", value: elemento.nome, maxlength: "120", required: true });
    const errorEl = el("p", { class: "pe-inline-error", role: "alert", hidden: true });
    const saveBtn = el("button", {
      type: "button",
      class: "pe-action",
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
          const result = await updateElemento(elemento.id, {
            strumento: elemento.strumento,
            nome,
            inputs: elemento.inputs,
            sintesi: elemento.sintesi,
            stato: elemento.stato,
            modalita: elemento.modalita,
            provenienza: elemento.provenienza,
            revisione: elemento.revisione,
          });
          if (result.conflict) {
            errorEl.textContent = result.message || "Modificato da un altro utente: ricarica e riprova.";
            errorEl.hidden = false;
            saveBtn.disabled = false;
            return;
          }
          replaceElemento(result.data);
          renderList();
        } catch (error) {
          errorEl.textContent = error.message || "Impossibile rinominare.";
          errorEl.hidden = false;
          saveBtn.disabled = false;
        }
      },
    });
    const cancelBtn = el("button", { type: "button", class: "pe-action", text: "Annulla", onclick: renderList });
    actionsHost.append(input, saveBtn, cancelBtn, errorEl);
    input.focus();
    input.select();
  }

  function buildDeleteConfirm(elemento, actionsHost) {
    clear(actionsHost);
    const errorEl = el("p", { class: "pe-inline-error", role: "alert", hidden: true });
    const confirmBtn = el("button", {
      type: "button",
      class: "pe-action pe-action--danger",
      text: "Conferma eliminazione",
      onclick: async () => {
        confirmBtn.disabled = true;
        try {
          const result = await deleteElemento(elemento.id, elemento.revisione);
          if (result.conflict) {
            errorEl.textContent = result.message || "Modificato da un altro utente: ricarica e riprova.";
            errorEl.hidden = false;
            confirmBtn.disabled = false;
            return;
          }
          removeElemento(elemento.id);
          renderList();
        } catch (error) {
          errorEl.textContent = error.message || "Impossibile eliminare.";
          errorEl.hidden = false;
          confirmBtn.disabled = false;
        }
      },
    });
    actionsHost.append(el("span", { class: "pe-inline-question", text: "Confermi l'eliminazione?" }), confirmBtn, el("button", { type: "button", class: "pe-action", text: "Annulla", onclick: renderList }), errorEl);
  }

  function openDuplicaForm(elemento, actionsHost) {
    clear(actionsHost);
    const input = el("input", { type: "text", class: "pe-rename-input", value: `${elemento.nome} (copia)`, maxlength: "120", required: true });
    const errorEl = el("p", { class: "pe-inline-error", role: "alert", hidden: true });
    const saveBtn = el("button", {
      type: "button",
      class: "pe-action",
      text: "Duplica",
      onclick: async () => {
        const nome = input.value.trim();
        if (!nome) {
          errorEl.textContent = "Il nome è obbligatorio.";
          errorEl.hidden = false;
          return;
        }
        saveBtn.disabled = true;
        try {
          const created = await duplicateElemento(elemento.id, nome);
          elementi = [created, ...elementi];
          buildFilterOptions();
          renderList();
        } catch (error) {
          errorEl.textContent = error.message || "Impossibile duplicare.";
          errorEl.hidden = false;
          saveBtn.disabled = false;
        }
      },
    });
    actionsHost.append(input, saveBtn, el("button", { type: "button", class: "pe-action", text: "Annulla", onclick: renderList }), errorEl);
    input.focus();
    input.select();
  }

  function buildActions(elemento, actionsHost) {
    clear(actionsHost);
    const tool = toolsByName.get(elemento.strumento);
    if (tool) {
      actionsHost.append(el("a", { class: "pe-action", href: `#/${encodeURIComponent(elemento.strumento)}?elemento=${encodeURIComponent(elemento.id)}`, text: "Apri" }));
    } else {
      actionsHost.append(el("span", { class: "pe-action pe-action--disabled", text: "Strumento non disponibile" }));
    }
    actionsHost.append(
      el("button", { type: "button", class: "pe-action", text: "Duplica", onclick: () => openDuplicaForm(elemento, actionsHost) }),
      el("button", { type: "button", class: "pe-action", text: "Rinomina", onclick: () => buildRenameForm(elemento, actionsHost) }),
      el("button", { type: "button", class: "pe-action", text: "Elimina", onclick: () => buildDeleteConfirm(elemento, actionsHost) }),
    );
  }

  function buildRow(elemento) {
    const tool = toolsByName.get(elemento.strumento);
    const chip = tool ? siglaChip(tool.sigla) : siglaChip(elemento.strumento.slice(0, 2).toUpperCase());
    const grid = el("div", { class: "pe-row-grid" }, [
      chip,
      el("span", { class: "pe-row-nome", text: elemento.nome, title: elemento.nome }),
      el("span", { class: `pe-stato pe-stato--${elemento.stato}`, text: STATO_LABELS[elemento.stato] || elemento.stato }),
      el("span", { class: "pe-row-eta", text: etaMaxText(elemento) }),
      el("span", { class: "pe-row-governante", text: (elemento.sintesi && elemento.sintesi.verifica_governante) || "—", title: (elemento.sintesi && elemento.sintesi.verifica_governante) || "" }),
      el("span", { class: "pe-row-updated", text: formatDate(elemento.aggiornato) }),
    ]);
    const actionsHost = el("div", { class: "pe-row-actions" });
    buildActions(elemento, actionsHost);
    const row = el("li", { class: "pe-row", "data-id": elemento.id }, [grid, actionsHost, buildProgettoStoria(elemento)]);
    return row;
  }

  function renderList() {
    clear(listHost);
    const visible = visibleElementi();
    if (visible.length === 0) {
      listHost.append(el("p", { class: "pe-empty", text: "Nessun elemento salvato per questo progetto." }));
      return;
    }
    const list = el("ul", { class: "pe-list" });
    for (const elemento of visible) list.append(buildRow(elemento));
    listHost.append(list);
  }

  filterSelect.addEventListener("change", () => {
    filterStrumento = filterSelect.value;
    renderList();
  });

  Promise.all([fetchElementi(progetto.id), fetchTools().catch(() => [])])
    .then(([elenco, tools]) => {
      elementi = elenco;
      toolsByName = new Map(tools.map((tool) => [tool.name, tool]));
      buildFilterOptions();
      renderList();
    })
    .catch((error) => setError(error.message || "Impossibile caricare gli elementi del progetto."));
}
