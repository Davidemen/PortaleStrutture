// #/registro (WORKBENCH_SPEC §13.1): every place the tool departs from the original spreadsheet,
// grouped by unit, filterable via the hash query so a filtered view is shareable. The shell
// renders this full-width, with no Dati/Sintesi split (js/main.js `showRegistro`).
import { el, clear } from "./dom.js";
import { fetchTools } from "./api.js";
import { fetchDivergenze, signoffMultiplo } from "./registro-api.js";
import { buildRegistroRow, TIPO_LABELS } from "./registro-row.js";
import { buildSignoffForm } from "./registro-signoff.js";
import { navigate } from "./router.js";

const STATI = ["da_confermare", "approvato", "respinto"];
const STATE_STRIP_LABELS = { da_confermare: "Da confermare", approvato: "Approvate", respinto: "Respinte" };
const SEARCH_DEBOUNCE_MS = 250;

function unitLabel(slug) {
  const spaced = slug.replace(/-/g, " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function groupByUnit(entries) {
  const groups = new Map();
  for (const entry of entries) {
    const key = entry.id.split("/", 1)[0];
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(entry);
  }
  return groups;
}

function emptyTotali() {
  return { da_confermare: 0, approvato: 0, respinto: 0 };
}

function countByState(entries) {
  const totals = emptyTotali();
  for (const entry of entries) totals[entry.stato] = (totals[entry.stato] || 0) + 1;
  return totals;
}

export function renderRegistro(root, { params = {} } = {}) {
  clear(root);
  let toolsByName = new Map();
  let entries = []; // every entry matching strumento/tipo/q, EVERY stato -- the totals strip needs all three counts regardless of which one is active
  let totali = emptyTotali();
  let selected = new Set();
  let searchTimer = null;
  const filters = {
    strumento: params.strumento || "",
    tipo: params.tipo || "",
    stato: params.stato || "",
    q: params.q || "",
    excelNo: params.excel === "no",
  };

  root.append(
    el("h2", { text: "Registro correzioni" }),
    el("p", { class: "reg-intro", text: "Ogni punto in cui lo strumento si discosta dal foglio Excel originale. Il progettista conferma o respinge ogni correzione." })
  );
  const errorHost = el("div", { class: "reg-error", role: "alert", hidden: true });
  const totalsStrip = el("div", { class: "reg-totals" });
  const filterRow = el("div", { class: "reg-filters" });
  const bulkBar = el("div", { class: "reg-bulk-bar", hidden: true });
  const listHost = el("div", { class: "reg-list-host" });
  root.append(errorHost, totalsStrip, filterRow, bulkBar, listHost);

  const searchInput = el("input", {
    type: "search", id: "reg-search", class: "reg-search", value: filters.q,
    placeholder: "Cerca nel registro", "aria-label": "Cerca nel registro",
  });
  const strumentoSelect = el("select", { id: "reg-strumento", class: "reg-select", "aria-label": "Filtra per strumento" });
  strumentoSelect.append(el("option", { value: "", text: "Tutti gli strumenti" }));
  const tipoSelect = el("select", { id: "reg-tipo", class: "reg-select", "aria-label": "Filtra per tipo" });
  tipoSelect.append(el("option", { value: "", text: "Tutti i tipi" }));
  for (const [value, label] of Object.entries(TIPO_LABELS)) tipoSelect.append(el("option", { value, text: label }));
  tipoSelect.value = filters.tipo;
  // "A filter chip 'Non riprodotte in Excel' next to the tipo select" (WORKBENCH_SPEC §13.1):
  // client-side only (ramo never reaches the server as a filter param), reflected in the hash
  // query as `excel=no` so it stays shareable like every other filter here.
  const excelChip = el("button", {
    type: "button", class: "reg-excel-chip", "aria-pressed": String(filters.excelNo),
    text: "Non riprodotte in Excel",
  });
  excelChip.addEventListener("click", () => {
    filters.excelNo = !filters.excelNo;
    excelChip.setAttribute("aria-pressed", String(filters.excelNo));
    pushRoute();
    renderList();
  });
  filterRow.append(
    el("div", { class: "reg-filter-field" }, [el("label", { for: "reg-search", text: "Cerca" }), searchInput]),
    el("div", { class: "reg-filter-field" }, [el("label", { for: "reg-strumento", text: "Strumento" }), strumentoSelect]),
    el("div", { class: "reg-filter-field" }, [el("label", { for: "reg-tipo", text: "Tipo" }), tipoSelect]),
    el("div", { class: "reg-filter-field reg-filter-field--chip" }, [excelChip])
  );

  function pushRoute() {
    const query = {};
    if (filters.strumento) query.strumento = filters.strumento;
    if (filters.tipo) query.tipo = filters.tipo;
    if (filters.stato) query.stato = filters.stato;
    if (filters.q) query.q = filters.q;
    if (filters.excelNo) query.excel = "no";
    navigate("registro", query, { replace: true });
  }

  function setError(message) {
    errorHost.hidden = !message;
    errorHost.textContent = message || "";
  }

  function renderTotalsStrip() {
    clear(totalsStrip);
    for (const stato of STATI) {
      const active = filters.stato === stato;
      const btn = el("button", {
        type: "button", class: "reg-total-btn", "aria-pressed": String(active),
        text: `${STATE_STRIP_LABELS[stato]} ${totali[stato] || 0}`,
      });
      btn.addEventListener("click", () => {
        filters.stato = active ? "" : stato;
        pushRoute();
        renderTotalsStrip();
        renderList();
      });
      totalsStrip.append(btn);
    }
  }

  function visibleEntries() {
    let list = filters.stato ? entries.filter((entry) => entry.stato === filters.stato) : entries;
    if (filters.excelNo) list = list.filter((entry) => entry.ramo === "nessuno");
    return list;
  }

  function onRowChanged(updatedEntry) {
    entries = entries.map((entry) => (entry.id === updatedEntry.id ? updatedEntry : entry));
    totali = countByState(entries);
    renderTotalsStrip();
    document.dispatchEvent(new CustomEvent("strutture:registro-changed"));
  }

  function buildCheckbox(entry) {
    const checkbox = el("input", { type: "checkbox", class: "reg-row-check", "aria-label": `Seleziona «${entry.titolo}»` });
    checkbox.checked = selected.has(entry.id);
    checkbox.addEventListener("change", () => {
      const next = new Set(selected);
      if (checkbox.checked) next.add(entry.id);
      else next.delete(entry.id);
      selected = next;
      buildBulkBar();
    });
    return checkbox;
  }

  // Left OPEN (not torn down) on a successful bulk save, same reasoning as registro-row.js's own
  // form: the `role=status` "Decisione salvata." confirmation lives in THIS panel, and rebuilding
  // it immediately would remove it before the engineer ever saw it.
  function buildBulkBar() {
    clear(bulkBar);
    if (selected.size === 0) {
      bulkBar.hidden = true;
      return;
    }
    bulkBar.hidden = false;
    const opener = el("button", {
      type: "button", class: "reg-bulk-btn", "aria-expanded": "false",
      text: `Decidi per le ${selected.size} selezionate…`,
    });
    const panelHost = el("div", { class: "reg-bulk-panel", hidden: true });
    opener.addEventListener("click", () => {
      const open = panelHost.hidden;
      opener.setAttribute("aria-expanded", String(open));
      panelHost.hidden = !open;
      if (!open) return;
      clear(panelHost);
      const { form } = buildSignoffForm({
        idPrefix: "reg-bulk",
        submitLabel: "Applica alle selezionate",
        onSubmit: (payload) =>
          signoffMultiplo({ ids: [...selected], ...payload }).then(() => {
            const ids = selected;
            entries = entries.map((entry) => (ids.has(entry.id) ? { ...entry, stato: payload.stato, sigla: payload.sigla, nota: payload.nota } : entry));
            totali = countByState(entries);
            renderTotalsStrip();
            renderList();
            document.dispatchEvent(new CustomEvent("strutture:registro-changed"));
          }),
      });
      panelHost.append(form);
    });
    bulkBar.append(opener, panelHost);
  }

  function renderList() {
    clear(listHost);
    const visible = visibleEntries();
    if (visible.length === 0) {
      listHost.append(el("p", { class: "reg-empty", text: "Nessuna correzione per questi filtri." }));
      return;
    }
    for (const [unit, unitEntries] of groupByUnit(visible)) {
      listHost.append(
        el("h3", { class: "reg-group-heading", text: `${unitLabel(unit)} · ${unitEntries.length} correzion${unitEntries.length === 1 ? "e" : "i"}` })
      );
      const ul = el("ul", { class: "reg-list" });
      for (const entry of unitEntries) {
        const { li } = buildRegistroRow(entry, { toolsByName, checkbox: buildCheckbox(entry), onChanged: onRowChanged });
        ul.append(li);
      }
      listHost.append(ul);
    }
    if (params.id) {
      const targetLi = listHost.querySelector(`[data-id="${CSS.escape(params.id)}"]`);
      const toggle = targetLi ? targetLi.querySelector(".reg-row-toggle") : null;
      if (toggle && toggle.getAttribute("aria-expanded") !== "true") toggle.click();
      if (targetLi) targetLi.scrollIntoView({ block: "center" });
    }
  }

  function load() {
    setError(null);
    fetchDivergenze({ strumento: filters.strumento, tipo: filters.tipo, q: filters.q })
      .then((body) => {
        entries = body.divergenze;
        totali = body.totali;
        renderTotalsStrip();
        renderList();
      })
      .catch((error) => setError(error.message || "Impossibile caricare il registro delle correzioni."));
  }

  searchInput.addEventListener("input", () => {
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      filters.q = searchInput.value;
      pushRoute();
      load();
    }, SEARCH_DEBOUNCE_MS);
  });
  strumentoSelect.addEventListener("change", () => {
    filters.strumento = strumentoSelect.value;
    pushRoute();
    load();
  });
  tipoSelect.addEventListener("change", () => {
    filters.tipo = tipoSelect.value;
    pushRoute();
    load();
  });

  renderTotalsStrip();

  fetchTools()
    .then((tools) => {
      toolsByName = new Map(tools.map((tool) => [tool.name, tool]));
      for (const tool of tools) strumentoSelect.append(el("option", { value: tool.name, text: `${tool.sigla} — ${tool.title}` }));
      strumentoSelect.value = filters.strumento;
    })
    .catch(() => {
      /* the tool select degrades to "Tutti gli strumenti" only -- filtering by name is still possible via `q` */
    })
    .finally(() => load());
}
