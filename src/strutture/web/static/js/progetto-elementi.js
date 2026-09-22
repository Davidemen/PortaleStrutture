// The element list of a project page (WORKBENCH_SPEC §14.3 -> §20 the table): fetches elements,
// tools and the project's §25 stato once, then mounts js/progetto-tabella.js for the active
// elements (sort/filter/Azioni all live there now) plus a small "Mostra eliminati" toggle that
// reveals soft-deleted rows in a plain list (unchanged from before the table, since §20 is only
// about the live element table).
import { el, clear } from "./dom.js";
import { fetchTools } from "./api.js";
import { fetchElementi, restoreElemento } from "./progetti-api.js";
import { renderProgettoTabella } from "./progetto-tabella.js";
import { fetchStatoProgetto, setStatoProgetto, renderProgettoStatoHead } from "./progetto-stato.js";

export const STATO_LABELS = { verificato: "✓ Verificato", non_verificato: "✕ Non verificato", dati_modificati: "○ Dati modificati" };

function formatDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" });
}

function buildDeletedRow(elemento, onRestored) {
  const restoreBtn = el("button", {
    type: "button", class: "pe-action", text: "Ripristina",
    onclick: async () => {
      try {
        onRestored(await restoreElemento(elemento.id));
      } catch (error) {
        errorHost.hidden = false;
        errorHost.textContent = error.message || "Impossibile ripristinare.";
      }
    },
  });
  const errorHost = el("span", { class: "pe-inline-error", role: "alert", hidden: true });
  return el("li", { class: "pe-row pe-row--deleted", "data-id": elemento.id }, [
    el("span", { class: "pe-row-nome", text: elemento.nome }),
    el("span", { class: "pe-stato pe-stato--eliminato", text: "⊘ Eliminato" }),
    el("span", { class: "pe-row-updated", text: formatDate(elemento.aggiornato) }),
    restoreBtn,
    errorHost,
  ]);
}

export function renderProgettoElementi(root, { progetto, params = {} } = {}) {
  clear(root);
  let elementi = [];
  let toolsByName = new Map();
  let showDeleted = false;
  let statoRequestId = 0; // discards an in-flight refreshStato() answered out of order
  // "last mount wins" owner token (same pattern as js/varianti-confronto.js's `root._smOwner`):
  // the `strutture:registro-changed` listener below is added once per render call but must stop
  // acting the moment a LATER render (a different project, or a re-render of this one) replaces it.
  const owner = {};
  root._smOwner = owner;

  root.append(el("h3", { text: "Elementi" }));
  const errorHost = el("div", { class: "pe-error", role: "alert", hidden: true });
  const statoHeadHost = el("div", { class: "pe-stato-head" });
  const toggleRow = el("div", { class: "pe-toolbar" });
  const showDeletedToggle = el("button", { type: "button", class: "pe-toggle-deleted", "aria-pressed": "false", text: "Mostra eliminati" });
  toggleRow.append(showDeletedToggle);
  const tabellaHost = el("div", { class: "pe-tabella-host" });
  const deletedHost = el("ul", { class: "pe-list" });
  deletedHost.hidden = true;
  root.append(errorHost, statoHeadHost, toggleRow, tabellaHost, deletedHost);

  function setError(message) {
    errorHost.hidden = !message;
    errorHost.textContent = message || "";
  }

  function renderDeleted() {
    clear(deletedHost);
    const eliminati = elementi.filter((item) => item.eliminato);
    if (eliminati.length === 0) {
      deletedHost.append(el("li", { class: "pe-empty", text: "Nessun elemento eliminato." }));
      return;
    }
    for (const elemento of eliminati) {
      deletedHost.append(buildDeletedRow(elemento, (restored) => {
        elementi = elementi.map((item) => (item.id === restored.id ? restored : item));
        renderAll();
      }));
    }
  }

  function renderTabella() {
    renderProgettoTabella(tabellaHost, {
      progettoId: progetto.id,
      elementi: elementi.filter((item) => !item.eliminato),
      toolsByName,
      params,
      onChange: (next) => {
        // `next` is the table's own non-eliminated rows only (it never sees `eliminato` ones) --
        // merge by id rather than replacing wholesale, or every already-deleted element vanishes
        // from "Mostra eliminati" (it can no longer be restored) the moment the table itself
        // changes anything (Rinomina/Duplica/Elimina).
        const byId = new Map(next.map((item) => [item.id, item]));
        const stillEliminati = elementi.filter((item) => item.eliminato && !byId.has(item.id));
        elementi = [...next, ...stillEliminati];
        renderAll();
      },
    });
  }

  function refreshStato() {
    const requestId = ++statoRequestId;
    fetchStatoProgetto(progetto.id)
      .then((stato) => {
        if (requestId !== statoRequestId) return; // a later refreshStato() already answered
        setStatoProgetto(stato);
        renderProgettoStatoHead(statoHeadHost, stato.conteggi);
        renderTabella(); // badges read the just-set snapshot
      })
      .catch(() => {
        if (requestId !== statoRequestId) return;
        setStatoProgetto({ elementi: {}, conteggi: null });
        renderProgettoStatoHead(statoHeadHost, null);
        setError("Stato del progetto non disponibile.");
      });
  }

  function renderAll() {
    renderTabella();
    if (showDeleted) renderDeleted();
    refreshStato();
  }

  showDeletedToggle.addEventListener("click", () => {
    showDeleted = !showDeleted;
    showDeletedToggle.setAttribute("aria-pressed", String(showDeleted));
    deletedHost.hidden = !showDeleted;
    if (showDeleted) renderDeleted();
  });

  // §25.3: a registro signoff can flip da_confermare/respinto counts for THIS project's own
  // elements without anything here having changed them -- refetch stato (never the elements
  // themselves, which the registro cannot touch) so provvisorio/da_ricalcolare badges catch up.
  document.addEventListener("strutture:registro-changed", () => {
    if (root._smOwner !== owner) return;
    refreshStato();
  });

  Promise.all([fetchElementi(progetto.id, { inclusiEliminati: true }), fetchTools().catch(() => [])])
    .then(([elenco, tools]) => {
      elementi = elenco;
      toolsByName = new Map(tools.map((tool) => [tool.name, tool]));
      renderTabella();
      refreshStato();
    })
    .catch((error) => setError(error.message || "Impossibile caricare gli elementi del progetto."));
}
