// Pure parsing helpers for the table-input widget: pasted TSV / ";"-CSV and uploaded CSV files.
// No DOM access here on purpose -- unit-testable with plain `node --check` / `node` scripts.
import { symbolText } from "./symbols.js";

function stripDiacritics(text) {
  return text.normalize("NFD").replace(/\p{Diacritic}/gu, "");
}

// Normalises a header cell (or a column name/label/alias) for case/accent/unit-insensitive matching.
export function normalizeHeaderCell(text) {
  return stripDiacritics(String(text))
    .toLowerCase()
    .replace(/[[(][^\])]*[\])]/g, " ") // drop bracketed units, e.g. "Fz (kN)"
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function detectDelimiter(lines) {
  if (lines.some((line) => line.includes("\t"))) return "\t";
  if (lines.some((line) => line.includes(";"))) return ";";
  return ",";
}

// Splits pasted/uploaded text into a grid of raw string cells, skipping blank lines.
export function parseDelimited(text) {
  const lines = String(text ?? "")
    .replace(/^﻿/, "") // strip a UTF-8 BOM if present
    .split(/\r\n|\r|\n/)
    .filter((line) => line.trim() !== "");
  if (lines.length === 0) return { rows: [], delimiter: "\t" };
  const delimiter = detectDelimiter(lines);
  const rows = lines.map((line) => line.split(delimiter).map((cell) => cell.trim()));
  return { rows, delimiter };
}

// Broad enough to recognise anything numeric-*shaped* (incl. rejected thousands grouping) as
// data rather than a header label, which only ever contains letters.
function isPlainNumeric(cell) {
  return /^-?\d[\d.,]*$/.test(cell.trim());
}

function candidateNames(column) {
  const names = [column.name, column.label, column.symbol, ...(column.aliases || [])];
  return names.filter(Boolean).map(normalizeHeaderCell);
}

// Maps a candidate header row onto columns using their `aliases`; falls back to position.
export function detectHeader(rows, columns) {
  if (rows.length === 0) return { hasHeader: false, mapping: columns.map((_, i) => i) };
  const first = rows[0];
  const headerLikely = columns.some(
    (column, i) => column.kind === "number" && first[i] && first[i].trim() !== "" && !isPlainNumeric(first[i]),
  );
  if (!headerLikely) return { hasHeader: false, mapping: columns.map((_, i) => i) };
  const mapping = columns.map((column, i) => {
    const wanted = candidateNames(column);
    const found = first.findIndex((cell) => wanted.includes(normalizeHeaderCell(cell)));
    return found === -1 ? i : found;
  });
  return { hasHeader: true, mapping };
}

// A single separator is decimal (comma or point); two kinds together, or repeats, are thousands grouping.
function hasThousandsGrouping(raw) {
  const dots = (raw.match(/\./g) || []).length;
  const commas = (raw.match(/,/g) || []).length;
  return dots + commas > 1;
}

export function parseNumberCell(raw) {
  const text = raw.trim();
  if (hasThousandsGrouping(text)) {
    return { error: "separatore delle migliaia non ammesso, usa solo virgola o punto decimale" };
  }
  const normalized = text.replace(",", ".");
  const value = Number(normalized);
  if (text === "" || !Number.isFinite(value)) {
    return { error: "valore numerico non valido" };
  }
  return { value };
}

function parseBooleanCell(raw) {
  const text = raw.trim().toLowerCase();
  if (["1", "si", "sì", "true", "vero", "x"].includes(text)) return { value: true };
  if (["0", "no", "false", "falso", ""].includes(text)) return { value: text === "" ? null : false };
  return { error: "valore booleano non riconosciuto (usa sì/no)" };
}

function parseEnumCell(raw, column) {
  const text = raw.trim();
  if (text === "") return { value: null };
  const match = (column.enumValues || []).find((value) => normalizeHeaderCell(String(value)) === normalizeHeaderCell(text));
  return match === undefined ? { error: `valore non tra quelli ammessi (${(column.enumValues || []).join(", ")})` } : { value: match };
}

export function parseCell(raw, column) {
  const text = (raw ?? "").trim();
  if (text === "") {
    return column.required ? { error: "valore mancante" } : { value: null };
  }
  if (column.kind === "number") return parseNumberCell(text);
  if (column.kind === "boolean") return parseBooleanCell(text);
  if (column.kind === "enum") return parseEnumCell(text, column);
  return { value: text };
}

// Parses raw pasted/uploaded text into typed row objects keyed by column name.
export function parseTable(text, columns) {
  const { rows } = parseDelimited(text);
  const { hasHeader, mapping } = detectHeader(rows, columns);
  const dataRows = hasHeader ? rows.slice(1) : rows;
  const errors = [];
  const parsedRows = dataRows.map((rawRow, rowIndex) => {
    const row = {};
    columns.forEach((column, columnIndex) => {
      const sourceIndex = mapping[columnIndex];
      const cell = sourceIndex === -1 ? "" : rawRow[sourceIndex] ?? "";
      const result = parseCell(cell, column);
      if (result.error) {
        errors.push({ row: rowIndex, column: column.name, message: result.error });
        row[column.name] = null;
      } else {
        row[column.name] = result.value;
      }
    });
    return row;
  });
  return { rows: parsedRows, errors, headerDetected: hasHeader };
}

// Header-only CSV, used by "Scarica modello CSV" -- same "symbol + label + [unit]" convention
// as the results table header (table.js), so a round-tripped export/import lines up visually.
export function buildCsvTemplate(columns) {
  return columns
    .map((column) => {
      const withUnit = column.unit ? `${column.label} [${column.unit}]` : column.label;
      const symbol = symbolText(column.symbol);
      return symbol ? `${symbol} ${withUnit}` : withUnit;
    })
    .join(";");
}
