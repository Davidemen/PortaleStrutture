// Toolbar (add row / paste-from-Excel / CSV import+template) and the post-render API
// (setTableValue / refreshUnitHeaders / readTableValue / setCellError) that other modules import
// against a built table-input `wrapper`. Split out of table-input.js (module-length guideline).
import { el } from "./dom.js";
import { parseTable, buildCsvTemplate } from "./table-paste.js";
import { sourceFor } from "./table-sources.js";

// `hooks` = {currentRows, setRows, applyParsed, message} bound by the caller (table-input.js) to
// its own live row state, so this module holds no row data itself.
export function buildToolbar(field, id, columns, table, hooks) {
  const { currentRows, setRows, applyParsed, message } = hooks;
  const minItems = field.minItems ?? 0;
  const maxItems = field.maxItems ?? Infinity;

  const addButton = el("button", {
    type: "button",
    class: "f-table-btn",
    text: "Aggiungi riga",
    hidden: Boolean(table.fixed_rows),
    onclick: () => {
      const rows = currentRows();
      if (rows.length >= maxItems) return message(`Massimo ${maxItems} righe.`);
      setRows([...rows, {}]);
    },
  });
  const toolbar = el("div", { class: "f-table-toolbar" }, [addButton]);

  // Generic import-source hook (table-sources.js): the widget only knows a name may resolve to
  // a lazily-loaded module -- it carries no per-source (e.g. MIDAS) code of its own.
  const source = sourceFor(table.source);
  if (source) {
    const importButton = el("button", {
      type: "button",
      class: "f-table-btn",
      text: source.buttonLabel,
      onclick: async () => {
        const importModule = await source.load();
        importModule.openImport({ field, columns, table, currentRows, setRows, message, trigger: importButton });
      },
    });
    toolbar.append(importButton);
  }

  if (table.paste !== false) {
    const textarea = el("textarea", { class: "f-table-paste-area", rows: 4, "aria-label": "Incolla dati da Excel" });
    const modeReplace = el("input", { type: "radio", name: `${id}-paste-mode`, value: "sostituisci", checked: true });
    const modeAppend = el("input", { type: "radio", name: `${id}-paste-mode`, value: "aggiungi" });
    toolbar.append(
      el("details", { class: "f-table-paste" }, [
        el("summary", { text: "Incolla da Excel" }),
        textarea,
        el("label", {}, [modeReplace, document.createTextNode(" Sostituisci")]),
        el("label", {}, [modeAppend, document.createTextNode(" Aggiungi")]),
        el("button", {
          type: "button",
          class: "f-table-btn",
          text: "Applica",
          onclick: () => applyParsed(parseTable(textarea.value, columns), modeReplace.checked ? "sostituisci" : "aggiungi"),
        }),
      ]),
    );
  }

  if (table.csv) {
    const fileInput = el("input", { type: "file", accept: ".csv,text/csv", class: "f-table-file" });
    fileInput.addEventListener("change", async () => {
      const file = fileInput.files[0];
      if (!file) return;
      applyParsed(parseTable(await file.text(), columns), "sostituisci");
      fileInput.value = "";
    });
    toolbar.append(
      el("label", { class: "f-table-btn" }, [document.createTextNode("Carica CSV"), fileInput]),
      el("button", { type: "button", class: "f-table-btn", text: "Scarica modello CSV", onclick: () => downloadCsvTemplate(field, columns) }),
    );
  }
  return toolbar;
}

function downloadCsvTemplate(field, columns) {
  const csv = `﻿${buildCsvTemplate(columns)}\r\n`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = el("a", { href: url, download: `${field.name}-modello.csv`, hidden: true });
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

// Programmatic fill: example load, restored inputs.
export function setTableValue(container, rows) {
  if (container._smSetRows) container._smSetRows(rows || []);
}

// Live header relabel when the model's `unit_selector` field changes (§4b D1); values unchanged.
// Re-renders (so future add/paste/CSV re-renders keep using the right unit).
export function refreshUnitHeaders(container, unitKey) {
  if (container._smSetUnitKey) container._smSetUnitKey(unitKey);
}

// The submitted payload value: array of typed row objects (also the source used while collapsed).
export function readTableValue(container) {
  return container._smCurrentRows ? container._smCurrentRows() : [];
}

// Marks a single cell invalid (located server/validation error), per DESIGN_SPEC §4b.
export function setCellError(container, rowIndex, columnName, message) {
  const rows = container.querySelectorAll("tr.f-table-row");
  const row = rows[rowIndex];
  if (!row) return;
  const previous = row.nextElementSibling;
  if (previous && previous.classList.contains("f-table-row-error")) previous.remove();
  const input = row.querySelector(`[data-col="${columnName}"]`);
  if (input) input.setAttribute("aria-invalid", message ? "true" : "false");
  if (message) {
    const column = (container._smTableColumns || []).find((c) => c.name === columnName);
    const label = column ? column.label : columnName;
    row.after(el("tr", { class: "f-table-row-error" }, [el("td", { colspan: String(row.children.length), text: `${label}: ${message}` })]));
  }
}
