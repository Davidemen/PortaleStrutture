// Print-only row-table rendering (WORKBENCH_SPEC §10): every row up to 2 000, unpaged, no copy/CSV
// actions. Beyond 2 000 rows: the envelope (first/last rows) plus any row where a `highlight`
// column reaches its min or max ("the governing rows"), with a note pointing at the CSV export for
// the rest -- a 20 000-row table is otherwise ~400 print pages. Reuses table.js's own `buildTable`
// (header/caption/cell formatting) instead of a second implementation of the same formatting.
// `policy` (WORKBENCH_SPEC §11 "Tabelle": `{righe: "tutte"|"prime"|"governanti", n}`) is the
// overlay's own user-chosen override of this default >2000-row behaviour -- "tutte" (or no
// policy, the §10 direct-print path) keeps the rule above unchanged.
import { el } from "./dom.js";
import { buildTable } from "./table.js";

const PRINT_MAX_ROWS = 2000;
const ENVELOPE_ROWS = 25;
const DEFAULT_PRIME_N = 50;

// Row indices where a highlighted column hits its extreme (min AND max -- "smaller is worse" is
// only a convention for utilisation ratios, not every highlighted column in general).
function governingIndices(rows, columns) {
  const indices = new Set();
  for (const column of columns || []) {
    if (!column.highlight) continue;
    let minI = -1;
    let maxI = -1;
    rows.forEach((row, i) => {
      const value = row[column.name];
      if (typeof value !== "number" || Number.isNaN(value)) return;
      if (minI === -1 || value < rows[minI][column.name]) minI = i;
      if (maxI === -1 || value > rows[maxI][column.name]) maxI = i;
    });
    if (minI !== -1) indices.add(minI);
    if (maxI !== -1) indices.add(maxI);
  }
  return indices;
}

function truncate(node, rows, policy) {
  if (policy && policy.righe === "prime") {
    const n = Math.max(1, Number(policy.n) || DEFAULT_PRIME_N);
    if (rows.length <= n) return { rows, note: null };
    return { rows: rows.slice(0, n), note: `Prime ${n} righe di ${rows.length} (scelta dell'utente) — Tabella completa disponibile in CSV` };
  }
  if (policy && policy.righe === "governanti") {
    const indices = [...governingIndices(rows, node.columns)].sort((a, b) => a - b);
    if (indices.length === 0 || indices.length >= rows.length) return { rows, note: null };
    return {
      rows: indices.map((i) => rows[i]),
      note: `Solo le righe governanti (scelta dell'utente) — Tabella completa di ${rows.length} righe disponibile in CSV`,
    };
  }
  if (rows.length <= PRINT_MAX_ROWS) return { rows, note: null };
  const keep = new Set();
  for (let i = 0; i < ENVELOPE_ROWS && i < rows.length; i++) keep.add(i);
  for (let i = Math.max(0, rows.length - ENVELOPE_ROWS); i < rows.length; i++) keep.add(i);
  for (const i of governingIndices(rows, node.columns)) keep.add(i);
  const kept = [...keep].sort((a, b) => a - b).map((i) => rows[i]);
  return { rows: kept, note: `Tabella completa di ${rows.length} righe disponibile in CSV` };
}

export function buildPrintTable(node, allRows, policy) {
  const { rows, note } = truncate(node, allRows, policy);
  const wrap = el("div", { class: "r-table-print" });
  wrap.append(buildTable(node, rows, null));
  if (note) wrap.append(el("p", { class: "r-table-note", text: note }));
  return wrap;
}
