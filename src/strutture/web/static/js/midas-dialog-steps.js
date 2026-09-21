// DOM builders for the 4 steps of the MIDAS import dialog (MIDAS.md §5), plus the node-list
// parser. Each step function takes the dialog's mutable `state` object (read/written in place,
// never reassigned -- table-input.js uses the same pattern for its own live row state) so
// free-typing inputs write straight into `state` with no re-render and never lose focus.
import { el, clear } from "./dom.js";
import { setMidasKey } from "./midas-key.js";

const STEP_LABELS = ["Connessione", "Combinazioni", "Appoggi", "Importa"];

export function buildStepper(current) {
  return el(
    "ul",
    { class: "midas-steps" },
    STEP_LABELS.map((label, i) => el("li", { text: `${i + 1}. ${label}`, ...(i + 1 === current ? { "aria-current": "step" } : {}) })),
  );
}

export function setAlert(alertEl, messages) {
  const list = Array.isArray(messages) ? messages : messages ? [messages] : [];
  alertEl.textContent = list.join(" ");
}

// "1, 5, 10-20" -> ascending unique node ids; an Italian message naming the first bad token.
export function parseNodeList(text) {
  const tokens = String(text || "").split(",").map((t) => t.trim()).filter((t) => t !== "");
  if (tokens.length === 0) return { nodes: [], error: "Indica almeno un nodo." };
  const nodes = new Set();
  for (const token of tokens) {
    const range = token.match(/^(\d+)\s*-\s*(\d+)$/);
    const single = token.match(/^(\d+)$/);
    if (single) {
      nodes.add(Number(single[1]));
    } else if (range) {
      const lo = Math.min(Number(range[1]), Number(range[2]));
      const hi = Math.max(Number(range[1]), Number(range[2]));
      for (let n = lo; n <= hi; n += 1) nodes.add(n);
    } else {
      return { nodes: [], error: `Valore non valido: «${token}» (usa numeri o intervalli come 10-20).` };
    }
  }
  return { nodes: Array.from(nodes).sort((a, b) => a - b), error: null };
}

export function connectionStep(state, actions) {
  const wrap = el("div");
  const product = el("select", { id: "midas-product" }, [
    el("option", { value: "gen", text: "Gen NX", selected: state.product === "gen" }),
    el("option", { value: "civil", text: "Civil NX", selected: state.product === "civil" }),
  ]);
  product.addEventListener("change", () => { state.product = product.value; });

  const baseUrl = el("input", { type: "text", id: "midas-base-url", placeholder: state.placeholderUrl, "aria-describedby": "midas-base-url-help" });
  baseUrl.value = state.baseUrl;
  baseUrl.addEventListener("input", () => { state.baseUrl = baseUrl.value; });

  wrap.append(
    el("div", { class: "midas-field" }, [el("label", { for: "midas-product", text: "Prodotto" }), product]),
    el("div", { class: "midas-field" }, [
      el("label", { for: "midas-base-url", text: "Base URL" }),
      baseUrl,
      el("p", { class: "midas-help", id: "midas-base-url-help", text: "Vedi Apps > API Settings in MIDAS." }),
    ]),
  );

  if (!state.serverKey) {
    // The key is set as a DOM PROPERTY below, never as an HTML attribute (MIDAS.md §2 rule 2):
    // `el()`'s attrs map would call setAttribute("value", ...), which serialises into the DOM.
    const key = el("input", { type: "password", id: "midas-key", autocomplete: "off", "aria-describedby": "midas-key-help" });
    key.value = state.keyValue;
    key.addEventListener("input", () => {
      state.keyValue = key.value;
      setMidasKey(key.value);
    });
    wrap.append(
      el("div", { class: "midas-field" }, [
        el("label", { for: "midas-key", text: "Chiave API personale" }),
        key,
        el("p", { class: "midas-help", id: "midas-key-help", text: "Conservata solo per questa scheda del browser." }),
      ]),
    );
  }

  wrap.append(
    el("button", { type: "button", class: "midas-btn", text: state.verifyBusy ? "Verifica…" : "Verifica connessione", disabled: state.verifyBusy, onclick: actions.verify }),
  );
  if (state.verified) {
    const v = state.verified;
    const productLabel = v.product === "civil" ? "Civil NX" : "Gen NX";
    const units = v.units ? `${v.units.force}/${v.units.dist}` : "—";
    wrap.append(el("p", { class: "midas-summary", text: `${productLabel} ${v.name || ""} ${v.version || ""} — unità ${units}` }));
  }
  return wrap;
}

function isActiveCombo(combo) {
  return combo.active !== "INACTIVE";
}

function matchesSearch(combo, search) {
  return !search || combo.name.toLowerCase().includes(search.toLowerCase());
}

function buildComboRow(combo, state) {
  const sel = state.selected[combo.table_name];
  const inputId = `midas-combo-${combo.table_name}`;
  const checkbox = el("input", { type: "checkbox", id: inputId, checked: sel.checked });
  checkbox.addEventListener("change", () => { sel.checked = checkbox.checked; });

  const famiglia = el("select", { "aria-label": `Famiglia per ${combo.name}` }, [
    el("option", { value: "", text: "—", selected: !sel.famiglia }),
    ...(state.famiglieOptions || []).map((f) => el("option", { value: f, text: f, selected: sel.famiglia === f })),
  ]);
  famiglia.addEventListener("change", () => { sel.famiglia = famiglia.value || null; });

  return el("div", { class: "midas-combo-row" }, [checkbox, el("label", { class: "midas-combo-name", for: inputId, text: combo.name }), famiglia]);
}

export function combinationsStep(state) {
  const wrap = el("div");
  if (state.combosBusy) {
    wrap.append(el("p", { class: "midas-help", text: "Caricamento combinazioni…" }));
    return wrap;
  }

  const search = el("input", { type: "search", class: "midas-search", "aria-label": "Cerca combinazione" });
  search.value = state.search;
  const listContainer = el("div");

  function renderList() {
    clear(listContainer);
    const visible = state.combinations.filter((c) => (!state.onlyActive || isActiveCombo(c)) && matchesSearch(c, state.search));
    if (visible.length === 0) {
      listContainer.append(el("p", { class: "midas-help", text: "Nessuna combinazione trovata." }));
      return;
    }
    const groups = new Map();
    visible.forEach((c) => {
      const key = c.classification || "Altro";
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(c);
    });
    groups.forEach((rows, classification) => {
      const allSelected = rows.every((c) => state.selected[c.table_name].checked);
      const selectAll = el("button", {
        type: "button",
        class: "midas-btn",
        text: allSelected ? "Deseleziona tutte" : "Seleziona tutte",
        onclick: () => {
          rows.forEach((c) => { state.selected[c.table_name].checked = !allSelected; });
          renderList();
        },
      });
      const groupEl = el("div", { class: "midas-group" }, [el("div", { class: "midas-group-head" }, [el("h3", { text: classification }), selectAll])]);
      rows.forEach((c) => groupEl.append(buildComboRow(c, state)));
      listContainer.append(groupEl);
    });
  }

  search.addEventListener("input", () => { state.search = search.value; renderList(); });
  const onlyActive = el("input", { type: "checkbox", id: "midas-only-active", checked: state.onlyActive });
  onlyActive.addEventListener("change", () => { state.onlyActive = onlyActive.checked; renderList(); });

  wrap.append(search, el("label", { class: "midas-toggle", for: "midas-only-active" }, [onlyActive, document.createTextNode(" Solo attive")]), listContainer);
  renderList();
  return wrap;
}

export function supportsStep(state) {
  const tuttiLabel = state.supportsCount == null ? "Tutti i nodi vincolati" : `Tutti i nodi vincolati (${state.supportsCount})`;
  const tutti = el("input", { type: "radio", name: "midas-supports-mode", id: "midas-supports-tutti", checked: state.supportsMode === "tutti" });
  tutti.addEventListener("change", () => { state.supportsMode = "tutti"; });

  const gruppoText = el("input", { type: "text", "aria-label": "Nome del gruppo struttura", placeholder: "Nome gruppo" });
  gruppoText.value = state.gruppo;
  const gruppo = el("input", { type: "radio", name: "midas-supports-mode", id: "midas-supports-gruppo", checked: state.supportsMode === "gruppo" });
  gruppo.addEventListener("change", () => { state.supportsMode = "gruppo"; });
  gruppoText.addEventListener("input", () => { state.gruppo = gruppoText.value; });
  gruppoText.addEventListener("focus", () => { gruppo.checked = true; state.supportsMode = "gruppo"; });

  const nodiText = el("input", { type: "text", "aria-label": "Elenco nodi", placeholder: "1, 5, 10-20" });
  nodiText.value = state.nodiText;
  const nodi = el("input", { type: "radio", name: "midas-supports-mode", id: "midas-supports-nodi", checked: state.supportsMode === "nodi" });
  nodi.addEventListener("change", () => { state.supportsMode = "nodi"; });
  nodiText.addEventListener("input", () => { state.nodiText = nodiText.value; });
  nodiText.addEventListener("focus", () => { nodi.checked = true; state.supportsMode = "nodi"; });

  return el("div", { class: "midas-radio-group" }, [
    el("div", { class: "midas-radio-option" }, [tutti, el("label", { for: "midas-supports-tutti", text: tuttiLabel })]),
    el("div", { class: "midas-radio-option" }, [gruppo, el("label", { for: "midas-supports-gruppo", text: "Gruppo struttura" }), gruppoText]),
    el("div", { class: "midas-radio-option" }, [nodi, el("label", { for: "midas-supports-nodi", text: "Nodi" }), nodiText]),
  ]);
}

export function importStep(state, actions) {
  const wrap = el("div");
  const sostituisci = el("input", { type: "radio", name: "midas-import-mode", id: "midas-mode-sostituisci", checked: state.importMode === "sostituisci" });
  sostituisci.addEventListener("change", () => { state.importMode = "sostituisci"; });
  const aggiungi = el("input", { type: "radio", name: "midas-import-mode", id: "midas-mode-aggiungi", checked: state.importMode === "aggiungi" });
  aggiungi.addEventListener("change", () => { state.importMode = "aggiungi"; });

  wrap.append(
    el("div", { class: "midas-radio-option" }, [sostituisci, el("label", { for: "midas-mode-sostituisci", text: "Sostituisci le righe esistenti" })]),
    el("div", { class: "midas-radio-option" }, [aggiungi, el("label", { for: "midas-mode-aggiungi", text: "Aggiungi alle righe esistenti" })]),
  );

  const selectedCount = Object.values(state.selected).filter((s) => s.checked).length;
  wrap.append(el("p", { class: "midas-help", text: `${selectedCount} combinazioni selezionate.` }));

  if (state.warnings.length > 0) {
    wrap.append(el("div", { class: "midas-warnings" }, [el("p", { text: "Avvisi:" }), el("ul", {}, state.warnings.map((w) => el("li", { text: w })))]));
  }
  if (!state.done) {
    wrap.append(
      el("button", {
        type: "button",
        class: "midas-btn-primary",
        text: state.importBusy ? "Importazione…" : "Importa",
        disabled: state.importBusy || selectedCount === 0,
        onclick: actions.runImport,
      }),
    );
  }
  return wrap;
}
