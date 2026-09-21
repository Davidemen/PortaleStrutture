// it-IT value formatting for the results sheet. Intl.NumberFormat("it-IT") only, per the brief:
// 4 significant digits by default, integers exact, scientific below 1e-4 / above 1e6, full
// precision kept in `title` and used verbatim (decimal comma) for copy/CSV.
const SUPERSCRIPT = { "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };

function toSuperscript(exponent) {
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

function fullPrecisionCell(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "boolean") return value ? "sì" : "no";
  if (typeof value === "number") return String(value).replace(".", ",");
  return String(value);
}

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
