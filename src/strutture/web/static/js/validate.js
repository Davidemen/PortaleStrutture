// Client-side (Italian) validation + mapping of server errors onto fields/cells.
// The form is `novalidate`: every range/required message rendered here, never a native tooltip.

export function isVisible(field, values) {
  if (!field.condition) return true;
  const { field: dependsOn, equals } = field.condition;
  return (equals || []).includes(values[dependsOn]);
}

function formatBound(value, unit) {
  const text = Number.isInteger(value) ? String(value) : String(value).replace(".", ",");
  return unit ? `${text} ${unit}` : text;
}

function validateNumber(field, value) {
  if (field.minimum != null && value < field.minimum) return `Valore minimo: ${formatBound(field.minimum, field.unit)}.`;
  if (field.exclusiveMin != null && value <= field.exclusiveMin) return `Deve essere maggiore di ${formatBound(field.exclusiveMin, field.unit)}.`;
  if (field.maximum != null && value > field.maximum) return `Valore massimo: ${formatBound(field.maximum, field.unit)}.`;
  if (field.exclusiveMax != null && value >= field.exclusiveMax) return `Deve essere minore di ${formatBound(field.exclusiveMax, field.unit)}.`;
  return null;
}

function rowLabel(field, row, index) {
  const key = field.table && field.table.key;
  const keyValue = key ? row[key] : undefined;
  return keyValue != null ? `${field.label}, ${key} ${keyValue}` : `${field.label}, riga ${index + 1}`;
}

// Only row-count bounds and missing required cells are checked client-side; per-cell numeric
// ranges are deliberately left to the server (DESIGN_SPEC §4b "located errors" -> `setCellError`
// marks the exact cell) rather than duplicated here -- otherwise a range violation would always
// be blocked before submission and the located-error path could never be exercised.
function validateTable(field, rows) {
  const messages = [];
  if (rows.length < (field.minItems || 0)) messages.push(`Servono almeno ${field.minItems} righe.`);
  if (field.maxItems != null && rows.length > field.maxItems) messages.push(`Massimo ${field.maxItems} righe.`);
  rows.forEach((row, index) => {
    for (const column of field.columns || []) {
      const value = row[column.name];
      if (column.required && (value === null || value === undefined)) {
        messages.push(`${rowLabel(field, row, index)}, ${column.label}: valore mancante.`);
      }
    }
  });
  return messages.length ? messages.join(" ") : null;
}

// Returns `{fieldName: message}`, only for fields that fail and are currently visible.
export function validateValues(fields, values) {
  const errors = {};
  for (const field of fields) {
    if (!isVisible(field, values)) continue;
    const value = values[field.name];
    if (field.kind === "table") {
      const message = validateTable(field, value || []);
      if (message) errors[field.name] = message;
      continue;
    }
    if (field.required && (value === null || value === undefined || value === "")) {
      errors[field.name] = "Campo obbligatorio.";
      continue;
    }
    if (value === null || value === undefined) continue;
    if (field.kind === "number" && typeof value === "number") {
      const message = validateNumber(field, value);
      if (message) errors[field.name] = message;
    }
  }
  return errors;
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Whole-word match only: a plain `includes()` would false-positive on short/common field names
// (e.g. a field literally named "a") appearing as an ordinary substring of unrelated prose.
function mentionsFieldName(message, name) {
  return new RegExp(`\\b${escapeRegExp(name)}\\b`, "i").test(message);
}

// Server errors arrive as "loc: messaggio" strings (`shared/tool.py::_message`).
export function parseServerErrors(errors, fieldNames) {
  const byField = {};
  const general = [];
  for (const raw of errors || []) {
    const separator = raw.indexOf(": ");
    // No "loc: " prefix (e.g. a bare model-level message): still try to attach it by scanning
    // the text for known field names (the comune/zona "specify exactly one of" case).
    const loc = separator === -1 ? "" : raw.slice(0, separator);
    const message = separator === -1 ? raw : raw.slice(separator + 2);
    const first = loc.split(".")[0];
    const matched = fieldNames.filter((name) => name === loc || name === first || mentionsFieldName(raw, name));
    if (matched.length === 0) {
      general.push(raw);
    } else {
      matched.forEach((name) => {
        byField[name] = byField[name] ? `${byField[name]} ${message}` : message;
      });
    }
  }
  return { byField, general };
}

// DESIGN_SPEC §4b: `Report.error_details = [{loc, message}]`. Preferred over string parsing
// when present; falls back to `parseServerErrors` when empty.
export function mapLocatedErrors(errorDetails, fieldNames) {
  const byField = {};
  const byTable = {};
  const general = [];
  for (const { loc, message } of errorDetails || []) {
    if (loc.length === 0) {
      // Model-level message (e.g. "specificare esattamente uno tra comune e zona"): summary
      // always gets it, and it additionally attaches to every named field mentioned in the
      // text (§3 verdict/error-summary bullet), same rule `parseServerErrors` applies below.
      general.push(message);
      fieldNames
        .filter((name) => mentionsFieldName(message, name))
        .forEach((name) => {
          byField[name] = byField[name] ? `${byField[name]} ${message}` : message;
        });
    } else if (loc.length >= 3 && fieldNames.includes(loc[0]) && typeof loc[1] === "number") {
      const [name, row, column] = loc;
      byTable[name] = byTable[name] || [];
      byTable[name].push({ row, column, message });
    } else if (fieldNames.includes(loc[0])) {
      byField[loc[0]] = byField[loc[0]] ? `${byField[loc[0]]} ${message}` : message;
    } else {
      general.push(`${loc.join(".")}: ${message}`);
    }
  }
  return { byField, byTable, general };
}
