// Stateless DOM builders for the table-input row editor (js/table-input.js): one cell control
// per column kind, the header cell, reading a control's typed value back out, arrow/enter grid
// navigation between cells, and one data row -- all parameterised, no closures over row state.
import { el } from "./dom.js";

export function cellControl(column, value) {
  if (column.kind === "boolean") {
    return el("input", { type: "checkbox", checked: Boolean(value), "data-col": column.name });
  }
  if (column.kind === "enum") {
    const select = el("select", { "data-col": column.name });
    if (!column.required) select.append(el("option", { value: "", text: "—" }));
    for (const option of column.enumValues || []) {
      select.append(el("option", { value: String(option), text: String(option), selected: value === option }));
    }
    return select;
  }
  return el("input", {
    type: column.kind === "number" ? "number" : "text",
    inputmode: column.kind === "number" ? "decimal" : undefined,
    step: column.step,
    value: value ?? "",
    "data-col": column.name,
  });
}

export function headerCell(column, unitKey) {
  const unit = (unitKey && column.unitOptions && column.unitOptions[unitKey]) || column.unit;
  const text = [column.symbol, column.label, unit ? `[${unit}]` : null].filter(Boolean).join(" ");
  return el("th", { scope: "col", text });
}

export function readCellValue(input, column) {
  if (column.kind === "boolean") return input.checked;
  if (input.tagName === "SELECT") return input.value === "" ? null : input.value;
  if (column.kind === "number") return input.value === "" ? null : Number(input.value);
  return input.value.trim() === "" ? null : input.value.trim();
}

export function focusNeighbour(tbody, cell, dRow, dCol) {
  const tr = cell.closest("tr");
  const rows = Array.from(tbody.querySelectorAll("tr.f-table-row"));
  const cells = Array.from(tr.querySelectorAll("[data-col]"));
  const targetRow = rows[rows.indexOf(tr) + dRow];
  const targetCol = targetRow ? Array.from(targetRow.querySelectorAll("[data-col]"))[cells.indexOf(cell) + dCol] : null;
  if (targetCol) targetCol.focus();
}

export function previewText(count) {
  return `${count} righe caricate. Modifica con «Incolla da Excel» o «Carica CSV».`;
}

// One editable row. `actions` = {onDuplicate, onMoveUp, onMoveDown, onDelete} (omitted when
// `table.fixed_rows`); each receives the `<tr>` so the caller can locate it among its siblings.
export function buildDataRow(tbody, values, columns, actions) {
  const tr = el("tr", { class: "f-table-row" });
  for (const column of columns) {
    const control = cellControl(column, values[column.name]);
    control.addEventListener("keydown", (event) => {
      const moves = { ArrowDown: [1, 0], Enter: [1, 0], ArrowUp: [-1, 0], ArrowRight: [0, 1], ArrowLeft: [0, -1] };
      const move = moves[event.key];
      if (!move || (event.key === "Enter" && event.shiftKey)) return;
      if ((event.key === "ArrowLeft" || event.key === "ArrowRight") && control.tagName === "SELECT") return;
      event.preventDefault();
      focusNeighbour(tbody, control, move[0], move[1]);
    });
    tr.append(el("td", {}, [control]));
  }
  if (actions) {
    tr.append(
      el("td", { class: "f-table-actions" }, [
        el("button", { type: "button", class: "f-table-btn", text: "Duplica", onclick: () => actions.onDuplicate(tr) }),
        el("button", { type: "button", class: "f-table-btn", text: "↑", onclick: () => actions.onMoveUp(tr) }),
        el("button", { type: "button", class: "f-table-btn", text: "↓", onclick: () => actions.onMoveDown(tr) }),
        el("button", { type: "button", class: "f-table-btn", text: "Elimina", onclick: () => actions.onDelete(tr) }),
      ]),
    );
  }
  return tr;
}
