// it-IT value formatting for the results sheet. Intl.NumberFormat("it-IT") only, per the brief:
// 4 significant digits by default, integers exact, scientific below 1e-4 / above 1e6, full
// precision kept in `title` and used verbatim (decimal comma) for copy/CSV.
const SUPERSCRIPT = { "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };

// Exported for js/relazione-formule-testo.js: the printed display factor ("...·10⁻³",
// docs/architecture-phase2.md §3) uses the SAME digit/minus-sign superscript mapping as every
// other scientific-notation value on the sheet, rather than a second translation table.
export function toSuperscript(exponent) {
  return String(exponent).split("").map((ch) => SUPERSCRIPT[ch] ?? ch).join("");
}

function splitScientific(value) {
  const exponent = Math.floor(Math.log10(Math.abs(value)));
  const mantissa = value / 10 ** exponent;
  return { mantissa, exponent };
}

function isScientificRange(value) {
  const abs = Math.abs(value);
  return abs !== 0 && (abs < 1e-4 || abs >= 1e6);
}

export function formatNumber(value, { significant = 4, integer = false } = {}) {
  if (typeof value !== "number" || Number.isNaN(value)) return String(value);
  if (value === 0) return "0";
  if (integer || Number.isInteger(value)) {
    return new Intl.NumberFormat("it-IT", { maximumFractionDigits: 0 }).format(value);
  }
  if (isScientificRange(value)) {
    const { mantissa, exponent } = splitScientific(value);
    const mantissaText = new Intl.NumberFormat("it-IT", { maximumSignificantDigits: significant }).format(mantissa);
    return `${mantissaText}·10${toSuperscript(exponent)}`;
  }
  return new Intl.NumberFormat("it-IT", { maximumSignificantDigits: significant }).format(value);
}

// {text, title}: `title` is always the full-precision string, for the `title=` attribute.
export function formatValue(value, node = {}) {
  if (value === null || value === undefined) return { text: "", title: "" };
  if (typeof value === "boolean") {
    const word = value ? "sì" : "no";
    return { text: word, title: word };
  }
  if (typeof value === "number") {
    return { text: formatNumber(value, { integer: Boolean(node.integer) }), title: String(value) };
  }
  return { text: String(value), title: String(value) };
}

// DOM version of formatNumber's scientific branch: real <sup>, for the results sheet.
export function valueNode(value, node = {}) {
  const fragment = document.createDocumentFragment();
  if (value === null || value === undefined) return fragment;
  if (typeof value === "boolean") {
    fragment.append(document.createTextNode(value ? "sì" : "no"));
    return fragment;
  }
  if (typeof value !== "number" || Number.isNaN(value)) {
    fragment.append(document.createTextNode(String(value)));
    return fragment;
  }
  const integer = Boolean(node.integer) || Number.isInteger(value);
  if (value !== 0 && !integer && isScientificRange(value)) {
    const { mantissa, exponent } = splitScientific(value);
    const mantissaText = new Intl.NumberFormat("it-IT", { maximumSignificantDigits: 4 }).format(mantissa);
    fragment.append(document.createTextNode(`${mantissaText}·10`));
    const sup = document.createElement("sup");
    sup.textContent = String(exponent);
    fragment.append(sup);
    return fragment;
  }
  fragment.append(document.createTextNode(formatNumber(value, { integer })));
  return fragment;
}

// Utilisation ratios (eta max, OR, OS, the utilisation bar's aria-label...) always show exactly
// two decimals, it-IT comma (WORKBENCH_SPEC finding D) -- distinct from formatNumber's 4
// significant-digit default, which produced noisy values like "0,8478" where the engineer only
// ever needs "0,85". Used everywhere a ratio is displayed: Sintesi, check rows, bottom bar,
// aria-labels.
const UTILISATION_FORMAT = new Intl.NumberFormat("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export function formatUtilisation(ratio) {
  if (typeof ratio !== "number" || Number.isNaN(ratio)) return "";
  return UTILISATION_FORMAT.format(ratio);
}

// "1 avviso" / "2 avvisi" -- correct Italian singular/plural (WORKBENCH_SPEC finding E), reused
// wherever a count of warnings/items is spoken in words.
export function formatCount(count, singular, plural) {
  return `${count} ${count === 1 ? singular : plural}`;
}

// Review finding 21: units straight from the backend are plain ASCII ("kN/m3", "cm2/m") -- a
// digit right after its own unit letter, with nothing alphanumeric following, is always an
// exponent ("m3" -> "m³") and never mistaken for a genuine unit character since no SI/derived
// structural unit ends in a bare digit any other way. Used at every place a unit string reaches
// the screen (results/highlight/Sintesi cells, the form's own unit suffix, printed Dati di
// ingresso, table headers, validation messages) -- never in a plain-text export (CSV/TSV/clipboard
// stay ASCII, the more portable form for pasting into Excel).
const UNIT_SUPERSCRIPT = { "2": "²", "3": "³", "4": "⁴" };
const UNIT_EXPONENT_RE = /([a-zA-Zα-ωΑ-Ω])([234])(?![a-zA-Z0-9])/g;
export function formatUnit(unit) {
  if (!unit) return unit || "";
  return String(unit).replace(UNIT_EXPONENT_RE, (_, letter, digit) => `${letter}${UNIT_SUPERSCRIPT[digit]}`);
}

// Review finding 21: a check's `detail` is free Italian text built server-side with plain ASCII
// ("OS=1.263 (soglia γR=1.10)", "As,o=1570.8 mm² >= As,min=330.5 mm²") -- `>=`/`<=` become ≥/≤ and
// every DECIMAL point (a digit immediately on both sides -- never a clause-style "6.5.3", which
// `verdict.js` keeps in the separate `clause` field this is never applied to) becomes a comma, the
// same it-IT convention `formatNumber` already uses for every other value on the sheet. A unit
// already embedded in the text (e.g. "mm²") gets its own exponent normalised too.
export function formatDetail(detail) {
  if (!detail) return detail || "";
  // Review finding 8, same class of bug in `detail` rather than `name`: a raw variable-name
  // reference ("s_max", never re-cased -- unlike verdict.js's own check-name fallback, this text
  // is a free sentence already, not a single label) can appear inline ("s=150,0 mm vs s_max=...").
  const withoutUnderscore = String(detail).replace(/_/g, " ");
  const withComparisons = withoutUnderscore.replace(/>=/g, "≥").replace(/<=/g, "≤");
  const withCommas = withComparisons.replace(/(\d)\.(\d)/g, "$1,$2");
  return formatUnit(withCommas);
}

// Review finding 19: a highlight with no `symbol` hint falls back to its plain description -- for
// the rare field whose backend key is itself already upper-case (output-schema.js `humanize()`
// only ever capitalises the FIRST letter, leaving the rest of an already-shouting raw key
// untouched), that read as a tracked ALL-CAPS label, out of step with the sentence-case copy rule
// everywhere else. Only triggers on a string that is ENTIRELY upper-case (has no lower-case form
// of itself) -- an ordinary, already-correct Italian sentence with a mid-string acronym is
// returned untouched.
export function sentenceCase(text) {
  if (!text) return text;
  const isShouting = text === text.toUpperCase() && text !== text.toLowerCase();
  if (!isShouting) return text;
  const lower = text.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

function fullPrecisionCell(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "boolean") return value ? "sì" : "no";
  if (typeof value === "number") return String(value).replace(".", ",");
  return String(value);
}

// Full-precision, decimal-comma text for the click-to-copy interaction on a result value
// (WORKBENCH_SPEC #4) -- same rule CSV/TSV cells already use, exported so results-groups.js and
// sintesi.js don't reimplement it.
export const formatCopyValue = fullPrecisionCell;

function escapeField(text, separator) {
  if (text.includes(separator) || text.includes('"') || text.includes("\n")) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

// columns: [{key, header}]; both full precision, decimal comma, for Excel it-IT.
export function toCsv(rows, columns) {
  const sep = ";";
  const lines = [columns.map((c) => escapeField(c.header, sep)).join(sep)];
  for (const row of rows) {
    lines.push(columns.map((c) => escapeField(fullPrecisionCell(row[c.key]), sep)).join(sep));
  }
  return lines.join("\r\n");
}

export function toTsv(rows, columns) {
  const sep = "\t";
  const lines = [columns.map((c) => c.header).join(sep)];
  for (const row of rows) {
    lines.push(columns.map((c) => fullPrecisionCell(row[c.key])).join(sep));
  }
  return lines.join("\n");
}
