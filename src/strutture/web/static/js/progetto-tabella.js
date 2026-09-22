// Element table of `#/progetti/<id>` (WORKBENCH_SPEC §20.2): sortable, filterable, keyboard-driven.
// Row model/sort/filter logic lives in js/progetto-tabella-dati.js (pure, node-testable); this
// module owns the DOM, the header sort buttons, roving focus, the query-string sync and the
// per-row Azioni menu (Duplica/Rinomina/Storia/Elimina|Ripristina -- moved here from the old
// js/progetto-elementi.js row actions, §20.2).
import { el, clear } from "./dom.js";
import { siglaChip } from "./nav-state.js";
import { formatUtilisation } from "./format.js";
import { navigate } from "./router.js";
import { buildRows, filterRows, sortRows, footerCounts, ESITO_LABELS, SORT_DEFAULT } from "./progetto-tabella-dati.js";
import { renderProgettoStatoBadges, statoElementiSnapshot } from "./progetto-stato.js";
import { buildAzioniMenu } from "./progetto-tabella-azioni.js";
import { buildBar } from "./verdict.js";

const COLONNE = [
  { key: "strumento", label: "Strumento", sortable: true },
  { key: "nome", label: "Nome", sortable: true },
  { key: "eta", label: "η max", sortable: true },
  { key: "esito", label: "Esito", sortable: true },
  { key: "avvisi", label: "Avvisi", sortable: true },
  { key: "aggiornato", label: "Ultima revisione", sortable: true },
  { key: "azioni", label: "Azioni", sortable: false },
];

function formatDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" });
}

function etaText(row) {
  return row.etaMax === null ? "—" : formatUtilisation(row.etaMax);
}

function avvisiText(row) {
  if (row.avvisi.nd) return "n.d.";
  if (row.avvisi.n === 0) return "Nessuno";
  return `${row.avvisi.n} · ${row.avvisi.primo}`;
}

function avvisiTitle(row) {
  if (row.avvisi.nd) return "Riepilogo salvato con una versione precedente: apri e salva l'elemento per aggiornarlo";
  return row.avvisi.primo || "";
}

// hash query for `#/progetti/<id>?...` -- built/read the same way js/router.js's own `params`
// already flow through js/progetto.js -> js/progetto-elementi.js -> here.
function queryFromState(state) {
  const query = {};
  if (state.ordina !== SORT_DEFAULT.ordina) query.ordina = state.ordina;
  if (state.verso !== SORT_DEFAULT.verso) query.verso = state.verso;
  if (state.strumento) query.strumento = state.strumento;
  if (state.esito) query.esito = state.esito;
  if (state.stato) query.stato = state.stato;
  if (state.soloAvvisi) query.avvisi = "1";
  if (state.q) query.q = state.q;
  return query;
}

const STATO_FILTRO_LABELS = {
  "": "Tutti gli stati",
  da_ricalcolare: "↻ Da ricalcolare",
  provvisorio: "◐ Provvisorio",
  provvisorio_origine: "◐ Provvisorio per origine",
};

// One table is ever "live" at a time (same "last mount wins" pattern as js/annulla-ui.js/js/
// elemento-salva.js) -- js/progetto-stato.js's head-count buttons dispatch `strutture:progetto-
// filtro` rather than calling into a specific table instance directly, so the two stay decoupled.
let applyFiltroExterno = null;
document.addEventListener("strutture:progetto-filtro", (event) => {
  if (applyFiltroExterno) applyFiltroExterno(event.detail || {});
});

export function renderProgettoTabella(root, { progettoId, elementi, toolsByName, onChange, params = {} }) {
  clear(root);
  // The query survives Back/Forward/reload (§20.2): seeded from `root._smState` once this table
  // has already rendered once in this page instance, otherwise from the hash `params` the page
  // was opened with.
  const seed = root._smState || params;
  let state = {
    ordina: seed.ordina || SORT_DEFAULT.ordina,
    verso: seed.verso || SORT_DEFAULT.verso,
    strumento: seed.strumento || "",
    esito: seed.esito || "",
    stato: seed.stato || "",
    soloAvvisi: seed.avvisi === "1" || seed.soloAvvisi === true,
    q: seed.q || "",
  };

  function syncQuery() {
    root._smState = state;
    navigate(`progetti/${progettoId}`, queryFromState(state), { replace: true });
  }

  const filterRow = el("div", { class: "pt-filters" });
  const qInput = el("input", { type: "search", class: "pt-filter-q", value: state.q, "aria-label": "Cerca" });
  const strumentoSelect = el("select", { class: "pt-filter-strumento", "aria-label": "Strumento" });
  const esitoSelect = el("select", { class: "pt-filter-esito", "aria-label": "Esito" }, [
    el("option", { value: "", text: "Tutti gli esiti" }),
    ...Object.entries(ESITO_LABELS).map(([value, text]) => el("option", { value, text })),
  ]);
  const statoSelect = el("select", { class: "pt-filter-stato", "aria-label": "Stato" },
    Object.entries(STATO_FILTRO_LABELS).map(([value, text]) => el("option", { value, text })),
  );
  const avvisiCheck = el("input", { type: "checkbox", id: "pt-filter-avvisi" });
  const contatore = el("span", { class: "pt-filter-count" });
  const azzeraBtn = el("button", { type: "button", class: "pt-filter-clear", text: "Azzera filtri" });
  filterRow.append(
    el("label", { class: "pt-filter-label", text: "Cerca " }, [qInput]),
    strumentoSelect,
    esitoSelect,
    statoSelect,
    el("label", { class: "pt-filter-avvisi-label", for: "pt-filter-avvisi" }, [avvisiCheck, document.createTextNode(" Solo con avvisi")]),
    contatore,
    azzeraBtn,
  );

  const table = el("table", { class: "pt-table" });
  const caption = el("caption", { text: "Elementi del progetto" });
  const thead = el("thead");
  const tbody = el("tbody");
  table.append(caption, thead, tbody);
  const emptyMsg = el("p", { class: "pt-empty", hidden: true });
  const footer = el("p", { class: "pt-footer" });
  root.append(filterRow, table, emptyMsg, footer);

  function strumentiPresenti() {
    const seen = new Map();
    for (const elemento of elementi) {
      if (elemento.eliminato || seen.has(elemento.strumento)) continue;
      const tool = toolsByName.get(elemento.strumento);
      seen.set(elemento.strumento, tool ? `${tool.sigla} — ${tool.title}` : elemento.strumento);
    }
    return seen;
  }

  function buildFilterOptions() {
    clear(strumentoSelect);
    strumentoSelect.append(el("option", { value: "", text: "Tutti gli strumenti" }));
    for (const [name, label] of strumentiPresenti()) strumentoSelect.append(el("option", { value: name, text: label, selected: name === state.strumento }));
  }

  function visibleRows() {
    const rows = buildRows(elementi, toolsByName);
    const filtered = filterRows(rows, {
      q: state.q, strumento: state.strumento, esito: state.esito, soloAvvisi: state.soloAvvisi,
      stato: state.stato, statoElementi: statoElementiSnapshot(),
    });
    return sortRows(filtered, state.ordina, state.verso);
  }

  function headerButton(col) {
    if (!col.sortable) return el("th", { scope: "col", text: col.label });
    const active = state.ordina === col.key;
    const th = el("th", { scope: "col", "aria-sort": active ? (state.verso === "asc" ? "ascending" : "descending") : "none" });
    const btn = el("button", { type: "button", class: "pt-sort-btn", text: col.label + (active ? (state.verso === "asc" ? " ▲" : " ▼") : "") });
    btn.addEventListener("click", () => {
      if (state.ordina === col.key) {
        state = { ...state, verso: state.verso === "asc" ? "desc" : "asc" };
      } else {
        state = { ...state, ordina: col.key, verso: col.key === "eta" ? "desc" : "asc" };
      }
      syncQuery();
      renderAll();
    });
    th.append(btn);
    return th;
  }

  function renderHead() {
    clear(thead);
    const tr = el("tr");
    for (const col of COLONNE) tr.append(headerButton(col));
    thead.append(tr);
  }

  // row actions live in js/progetto-tabella-azioni.js (§20.2/§25.4, kept this module under the 400-line cap).

  function buildRow(row, rowIndex) {
    const tool = toolsByName.get(row.strumento);
    // An imported/legacy element whose tool no longer exists (§14.3's own "Apri" used to disable
    // itself the same way) has nothing to open -- plain text, no link, no row-click shortcut.
    const nomeChildren = tool
      ? [el("a", { href: `#/${encodeURIComponent(row.strumento)}?elemento=${encodeURIComponent(row.id)}`, text: row.nome, tabindex: "-1" })]
      : [document.createTextNode(row.nome), el("span", { class: "pe-action--disabled", text: " (strumento non disponibile)" })];
    if (row.elemento && row.elemento.sigla) {
      nomeChildren.push(document.createTextNode(" "), el("span", { class: "pt-cell-sigla", text: row.elemento.sigla }));
    }
    const nomeCell = el("td", { class: "pt-cell-nome" }, nomeChildren);
    const etaCell = el("td", { class: row.muted ? "pt-cell-eta pt-muted" : "pt-cell-eta" }, [
      document.createTextNode(`${row.muted ? "(prec.) " : ""}${etaText(row)}`),
      ...(row.etaMax === null ? [] : [buildBar(row.etaMax, row.esitoKey === "verificato")]),
    ]);
    const esitoCell = el("td", { class: "pt-cell-esito" });
    // §25.4: the provenance/state chips (provvisorio, da ricalcolare, ...) sit next to the esito,
    // not in a column of their own -- COLONNE above has exactly 7 headers, one per <td> here.
    // `renderProgettoStatoBadges` clears the cell itself, so the esito text is PREPENDED after it
    // runs, never set through `el()`'s own `text` option (which it would just wipe again).
    renderProgettoStatoBadges(esitoCell, row.elemento, toolsByName);
    esitoCell.prepend(document.createTextNode(`${ESITO_LABELS[row.esitoKey] || row.esitoKey} `));
    const avvisiCell = el("td", { class: row.muted ? "pt-cell-avvisi pt-muted" : "pt-cell-avvisi", text: `${row.muted ? "(prec.) " : ""}${avvisiText(row)}`, title: avvisiTitle(row) });
    const aggiornatoCell = el("td", { class: "pt-cell-aggiornato" }, [
      document.createTextNode(formatDate(row.aggiornato) + " "),
      el("span", { class: "pt-cell-rev", text: `rev. ${row.revisione}` }),
    ]);
    const azioniCell = el("td", { class: "pt-cell-azioni" });
    const statoVoce = statoElementiSnapshot()[row.id];
    const aggiornaOriginiUrl = `#/${encodeURIComponent(row.strumento)}?elemento=${encodeURIComponent(row.id)}&aggiorna_origini=1`;
    buildAzioniMenu({ elemento: row.elemento, cell: azioniCell, elementi, onChange, statoVoce, aggiornaOriginiUrl, toolsByName });
    const tr = el("tr", { class: "pt-row", "data-id": row.id }, [
      el("td", { class: "pt-cell-strumento", title: tool ? tool.title : row.strumento }, [siglaChip(row.siglaTool)]),
      nomeCell, etaCell, esitoCell, avvisiCell, aggiornatoCell, azioniCell,
    ]);
    tr.addEventListener("click", (event) => {
      if (!tool || event.target.closest("a, button, input, .pt-menu")) return;
      window.location.hash = `#/${encodeURIComponent(row.strumento)}?elemento=${encodeURIComponent(row.id)}`;
    });
    return tr;
  }

  function renderRows() {
    clear(tbody);
    const rows = visibleRows();
    if (rows.length === 0) {
      emptyMsg.hidden = false;
      emptyMsg.textContent = elementi.filter((e) => !e.eliminato).length === 0
        ? "Nessun elemento salvato per questo progetto."
        : "Nessun elemento corrisponde ai filtri.";
      table.hidden = true;
    } else {
      emptyMsg.hidden = true;
      table.hidden = false;
      rows.forEach((row, index) => tbody.append(buildRow(row, index)));
      const firstLink = tbody.querySelector(".pt-cell-nome a");
      if (firstLink) firstLink.tabIndex = 0;
    }
    return rows;
  }

  function renderFooter(rows) {
    const counts = footerCounts(rows);
    contatore.textContent = `${rows.length} di ${elementi.filter((e) => !e.eliminato).length} elementi`;
    const etaText2 = counts.etaMaxProgetto === null ? "" : ` · η max del progetto ${formatUtilisation(counts.etaMaxProgetto)} (${counts.etaMaxSigla})`;
    footer.textContent = `${counts.totale} elementi · ${counts.verificato} ✓ verificati · ${counts.non_verificato} ✕ non verificati · ${counts.dati_modificati} ○ dati modificati${etaText2}`;
  }

  function renderAll() {
    renderHead();
    const rows = renderRows();
    renderFooter(rows);
  }

  qInput.addEventListener("input", () => {
    state = { ...state, q: qInput.value };
    syncQuery();
    renderAll();
  });
  strumentoSelect.addEventListener("change", () => {
    state = { ...state, strumento: strumentoSelect.value };
    syncQuery();
    renderAll();
  });
  esitoSelect.addEventListener("change", () => {
    state = { ...state, esito: esitoSelect.value };
    syncQuery();
    renderAll();
  });
  statoSelect.addEventListener("change", () => {
    state = { ...state, stato: statoSelect.value };
    syncQuery();
    renderAll();
  });
  avvisiCheck.addEventListener("change", () => {
    state = { ...state, soloAvvisi: avvisiCheck.checked };
    syncQuery();
    renderAll();
  });
  function azzeraFiltri() {
    state = { ...SORT_DEFAULT, strumento: "", esito: "", stato: "", soloAvvisi: false, q: "" };
    qInput.value = "";
    strumentoSelect.value = "";
    esitoSelect.value = "";
    statoSelect.value = "";
    avvisiCheck.checked = false;
    syncQuery();
    renderAll();
  }
  azzeraBtn.addEventListener("click", azzeraFiltri);
  // Esc anywhere in the filter row clears every filter back to defaults (§25.4) -- never the
  // table body's own Esc-free roving focus below, and never a page-level Esc some dialog owns.
  filterRow.addEventListener("keydown", (event) => {
    if (event.key === "Escape") azzeraFiltri();
  });
  applyFiltroExterno = (patch) => {
    state = { ...state, ...patch };
    if (patch.esito !== undefined) esitoSelect.value = state.esito;
    if (patch.stato !== undefined) statoSelect.value = state.stato;
    syncQuery();
    renderAll();
  };

  // Roving focus (§20.2): Tab reaches the filters/header once, then ↑/↓ move focus across the
  // Nome links; Home/End jump to the first/last row; the context-menu key/Shift+F10 opens Azioni.
  esitoSelect.value = state.esito;
  statoSelect.value = state.stato;
  avvisiCheck.checked = state.soloAvvisi;
  buildFilterOptions();
  function moveRovingFocus(links, target) {
    if (!target) return;
    for (const link of links) link.tabIndex = -1;
    target.tabIndex = 0;
    target.focus();
  }
  tbody.addEventListener("keydown", (event) => {
    const links = Array.from(tbody.querySelectorAll(".pt-cell-nome a"));
    const current = document.activeElement;
    const index = links.indexOf(current);
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const next = event.key === "ArrowDown" ? Math.min(index + 1, links.length - 1) : Math.max(index - 1, 0);
      moveRovingFocus(links, links[next]);
    } else if (event.key === "Home") {
      event.preventDefault();
      moveRovingFocus(links, links[0]);
    } else if (event.key === "End") {
      event.preventDefault();
      moveRovingFocus(links, links[links.length - 1]);
    } else if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
      event.preventDefault();
      const row = current && current.closest("tr");
      const btn = row && row.querySelector(".pt-azioni-btn");
      if (btn) btn.click();
    }
  });
  renderAll();
}
