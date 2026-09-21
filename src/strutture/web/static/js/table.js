// Renders one row-tuple output field: sticky-head scrollable table, copy/CSV actions, and
// (when the `rows_page` hint is set) simple pager -- "Scarica CSV" always exports every row.
import { el, clear } from "./dom.js";
import { symbolNode, symbolText } from "./symbols.js";
import { formatValue, toCsv, toTsv, formatCopyValue, formatUnit } from "./format.js";
import { createCopyStatus, wireValueCopy } from "./results-toolbar.js";
import { copyText, buildManualCopyField } from "./clipboard.js";

const CSV_BOM = "﻿";
const LABEL_SWAP_MS = 2000;

function csvColumns(columns) {
  return columns.map((column) => ({ key: column.name, header: column.symbol ? symbolText(column.symbol) : column.label }));
}

// Columns that carry a `symbol` header as just the symbol + `[unit]` -- the full description
// moves to `title` (accessible name / hover tooltip) and into the one-line "Legenda" under the
// caption instead, so a table of 6+ such columns doesn't wrap into 5-line headers on mobile.
// Columns without a symbol keep their short description as the header text (nothing to shorten).
function headerRow(columns) {
  return el(
    "tr",
    {},
    columns.map((column) => {
      const th = el("th", { scope: "col", title: column.label, "aria-label": column.label });
      if (column.symbol) {
        th.append(symbolNode(column.symbol));
      } else {
        th.append(el("span", { class: "r-th-label", text: column.label }));
      }
      if (column.unit !== undefined) th.append(el("span", { class: "r-th-unit", text: `[${formatUnit(column.unit)}]` }));
      return th;
    })
  );
}

function symbolColumns(columns) {
  return columns.filter((column) => column.symbol);
}

// Compact legend line under the caption: lists each symbol-headed column's full description
// once, instead of repeating it in every header cell.
function buildLegendLine(columns) {
  const withSymbol = symbolColumns(columns);
  if (withSymbol.length === 0) return null;
  const p = el("p", { class: "r-table-legend" });
  p.append(document.createTextNode("Legenda: "));
  withSymbol.forEach((column, index) => {
    if (index > 0) p.append(document.createTextNode(" · "));
    p.append(symbolNode(column.symbol));
    p.append(document.createTextNode(` ${column.label}`));
  });
  return p;
}

function dataRow(columns, row, copyCtx) {
  return el(
    "tr",
    {},
    columns.map((column) => {
      const value = row[column.name];
      const { text, title } = formatValue(value, column);
      const td = el("td", { class: "r-num", text });
      if (title) td.title = title;
      if (copyCtx) wireValueCopy(td, formatCopyValue(value), copyCtx.announce);
      return td;
    })
  );
}

function swapLabel(button, text) {
  const original = button.textContent;
  button.textContent = text;
  setTimeout(() => {
    button.textContent = original;
  }, LABEL_SWAP_MS);
}

function triggerCsvDownload(filename, csv) {
  const blob = new Blob([CSV_BOM + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = el("a", { href: url, download: filename });
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function buildActions(node, allRows) {
  const bar = el("div", { class: "r-table-actions" });
  const copyBtn = el("button", { type: "button", class: "r-action", text: "Copia tabella" });
  copyBtn.addEventListener("click", async () => {
    const existing = bar.querySelector(":scope > .sm-clip-fallback");
    if (existing) existing.remove();
    const tsv = toTsv(allRows, csvColumns(node.columns));
    if (await copyText(tsv)) swapLabel(copyBtn, "Copiato");
    else bar.append(buildManualCopyField(tsv, "Tabella", { multiline: true }));
  });
  const csvBtn = el("button", { type: "button", class: "r-action", text: "Scarica CSV" });
  csvBtn.addEventListener("click", () => {
    triggerCsvDownload(`${node.toolName || "strumento"}-${node.name}.csv`, toCsv(allRows, csvColumns(node.columns)));
    swapLabel(csvBtn, "Scaricato");
  });
  bar.append(copyBtn, csvBtn);
  return bar;
}

// Exported so `relazione-table.js` (print, WORKBENCH_SPEC §10) can reuse the SAME header/caption/
// row formatting for an unpaged print table instead of a second implementation.
export function buildTable(node, pageRows, copyCtx) {
  const scroll = el("div", { class: "r-table-scroll", tabindex: "0", "aria-label": `Tabella: ${node.label}` });
  const table = el("table", { class: "r-table" });
  const caption = el("caption", {}, [document.createTextNode(node.label)]);
  const legendLine = buildLegendLine(node.columns);
  if (legendLine) caption.append(legendLine);
  table.append(caption);
  table.append(el("thead", {}, [headerRow(node.columns)]));
  table.append(el("tbody", {}, pageRows.map((row) => dataRow(node.columns, row, copyCtx))));
  scroll.append(table);
  return scroll;
}

function buildPager(page, totalPages, onChange) {
  const pager = el("div", { class: "r-pager" });
  const prev = el("button", { type: "button", class: "r-action", text: "Pagina precedente" });
  if (page === 0) prev.disabled = true;
  prev.addEventListener("click", () => onChange(page - 1));
  const status = el("span", { class: "r-pager-status", text: `Pagina ${page + 1} di ${totalPages}` });
  const next = el("button", { type: "button", class: "r-action", text: "Pagina successiva" });
  if (page >= totalPages - 1) next.disabled = true;
  next.addEventListener("click", () => onChange(page + 1));
  pager.append(prev, status, next);
  return pager;
}

export function renderRows(root, node, rows) {
  clear(root);
  const copyCtx = createCopyStatus(root);
  root.append(buildActions(node, rows));

  const pageSize = node.rowsPage;
  const totalPages = pageSize ? Math.max(1, Math.ceil(rows.length / pageSize)) : 1;
  const holder = el("div", { class: "r-table-holder" });
  root.append(holder);

  let page = 0;
  function renderPage() {
    clear(holder);
    const pageRows = pageSize ? rows.slice(page * pageSize, page * pageSize + pageSize) : rows;
    holder.append(buildTable(node, pageRows, copyCtx));
    if (pageSize && totalPages > 1) {
      holder.append(
        buildPager(page, totalPages, (nextPage) => {
          page = Math.min(Math.max(nextPage, 0), totalPages - 1);
          renderPage();
        })
      );
    }
  }
  renderPage();
}
