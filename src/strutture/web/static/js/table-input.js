// Row-editor widget for array-of-objects input fields (soil layers, support reactions, ...).
// Structural changes (add/delete/move/paste/CSV) recompute the row array immutably and
// re-render; typing into a cell edits the live DOM input directly (no re-render per keystroke).
// Rendering primitives live in table-input-render.js, the toolbar + post-render API in
// table-input-events.js; this module only owns the live row state and wires the two together.
import { el, clear } from "./dom.js";
import { headerCell, buildDataRow, readCellValue } from "./table-input-render.js";
import { buildToolbar, setTableValue, refreshUnitHeaders, readTableValue, setCellError } from "./table-input-events.js";

function readGridRows(tbody, columns) {
  return Array.from(tbody.querySelectorAll("tr.f-table-row")).map((tr) => rowValuesOf(tr, columns));
}

function rowValuesOf(tr, columns) {
  const row = {};
  tr.querySelectorAll("[data-col]").forEach((input) => {
    const column = columns.find((c) => c.name === input.dataset.col);
    if (column) row[column.name] = readCellValue(input, column);
  });
  return row;
}

export function buildTableField(field, id, { onMessage } = {}) {
  const columns = field.columns || [];
  const table = field.table || {};
  const minItems = field.minItems ?? 0;
  const maxItems = field.maxItems ?? Infinity;
  const previewLimit = table.preview_rows ?? 50;
  const message = (text) => onMessage && onMessage(text || null);

  const wrapper = el("div", { class: "f-table", id, "data-field": field.name });
  const body = el("div", { class: "f-table-body" });
  let snapshot = []; // authoritative row data while collapsed; DOM is authoritative while editable
  let collapsed = false;
  let unitKey = null; // current `unit_selector` value, applied to column headers on re-render

  const currentRows = () => (collapsed ? snapshot : readGridRows(body, columns));

  function buildRowActions(tbody) {
    return {
      onDuplicate: (tr) => {
        const rows = readGridRows(tbody, columns);
        const index = Array.from(tbody.querySelectorAll("tr.f-table-row")).indexOf(tr);
        setRows([...rows.slice(0, index + 1), rowValuesOf(tr, columns), ...rows.slice(index + 1)]);
      },
      onMoveUp: (tr) => moveRow(tr, -1),
      onMoveDown: (tr) => moveRow(tr, 1),
      onDelete: (tr) => deleteRow(tr),
    };
  }

  function moveRow(tr, offset) {
    const rows = readGridRows(body, columns);
    const index = Array.from(tr.parentElement.querySelectorAll("tr.f-table-row")).indexOf(tr);
    const target = index + offset;
    if (target < 0 || target >= rows.length) return;
    const next = rows.slice();
    [next[index], next[target]] = [next[target], next[index]];
    setRows(next);
  }

  function deleteRow(tr) {
    const rows = readGridRows(body, columns);
    if (rows.length <= minItems) return message(`Servono almeno ${minItems} righe.`);
    const index = Array.from(tr.parentElement.querySelectorAll("tr.f-table-row")).indexOf(tr);
    setRows(rows.filter((_, i) => i !== index));
  }

  function renderGrid(rows) {
    collapsed = false;
    const thead = el("thead", {}, [el("tr", {}, columns.map((c) => headerCell(c, unitKey)))]);
    const tbody = el("tbody");
    clear(body);
    body.append(el("table", { class: "f-table-grid" }, [thead, tbody]));
    const actions = table.fixed_rows ? null : buildRowActions(tbody);
    rows.forEach((row) => tbody.append(buildDataRow(tbody, row, columns, actions)));
  }

  function renderCollapsed(rows) {
    collapsed = true;
    snapshot = rows;
    const previewed = rows.length <= 6 ? rows : [...rows.slice(0, 3), null, ...rows.slice(-3)];
    const thead = el("thead", {}, [el("tr", {}, columns.map((c) => headerCell(c, unitKey)))]);
    const tbody = el(
      "tbody",
      {},
      previewed.map((row) =>
        row
          ? el("tr", {}, columns.map((c) => el("td", { text: row[c.name] ?? "" })))
          : el("tr", {}, [el("td", { colspan: String(columns.length), text: "…" })]),
      ),
    );
    clear(body);
    body.append(
      el("p", { class: "f-table-preview-count", text: `${rows.length} righe caricate. Modifica con «Incolla da Excel» o «Carica CSV».` }),
      el("table", { class: "f-table-grid" }, [thead, tbody]),
    );
  }

  function setRows(rows) {
    if (rows.length > previewLimit) renderCollapsed(rows);
    else renderGrid(rows);
    message(rows.length < minItems ? `Servono almeno ${minItems} righe.` : rows.length > maxItems ? `Massimo ${maxItems} righe.` : null);
  }

  function applyParsed(parsed, mode) {
    const base = mode === "aggiungi" ? currentRows() : [];
    setRows([...base, ...parsed.rows]);
    if (parsed.errors.length > 0) {
      const first = parsed.errors[0];
      message(`${parsed.errors.length} celle non valide (riga ${first.row + 1}: ${first.message}).`);
    }
  }

  const toolbar = buildToolbar(field, id, columns, table, { currentRows, setRows, applyParsed, message });
  wrapper.append(toolbar, el("div", { class: "f-table-scroll", tabindex: "0" }, [body]));
  wrapper._smTableColumns = columns;
  wrapper._smSetRows = setRows;
  wrapper._smCurrentRows = currentRows;
  wrapper._smSetUnitKey = (key) => {
    unitKey = key;
    setRows(currentRows());
  };
  setRows(Array.isArray(field.default) ? field.default : []);
  return wrapper;
}

export { setTableValue, refreshUnitHeaders, readTableValue, setCellError };
