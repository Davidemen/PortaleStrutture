// Per-tool persistence: last inputs in localStorage, shared inputs in the URL hash params.
import { readJSON, writeJSON, remove } from "./storage.js";
import { parseListText, formatListText } from "./list-input.js";

function storageKey(tool) {
  return `sm.inputs.${tool}`;
}

// Tables above their own (or the default) `preview_rows` are never persisted (§4b): they can
// hold thousands of rows and would blow the localStorage quota / the share link.
function persistable(values, fields) {
  const byName = new Map(fields.map((field) => [field.name, field]));
  return Object.fromEntries(
    Object.entries(values).filter(([name, value]) => {
      const field = byName.get(name);
      if (!field || field.kind !== "table") return true;
      const limit = (field.table && field.table.preview_rows) ?? 50;
      return Array.isArray(value) ? value.length <= limit : true;
    }),
  );
}

// `fields` is optional (kept out of the §5 sketch signature) and only used to skip huge tables.
export function save(tool, values, fields = []) {
  return writeJSON(storageKey(tool), persistable(values, fields));
}

export function load(tool) {
  return readJSON(storageKey(tool), null);
}

// "Azzera dati" (WORKBENCH_SPEC §3 action bar): drop the persisted inputs for this tool only.
export function clearStored(tool) {
  remove(storageKey(tool));
}

// Only scalar (non-table) fields go into the shared link: tables can hold thousands of rows.
export function toParams(values, fields) {
  const params = {};
  for (const field of fields) {
    if (field.kind === "table") continue;
    const value = values[field.name];
    if (value === null || value === undefined || value === "") continue;
    if (field.kind === "list") {
      if (Array.isArray(value) && value.length > 0) params[field.name] = formatListText(value, field.itemKind);
      continue;
    }
    params[field.name] = String(value);
  }
  return params;
}

export function fromParams(params, fields) {
  const values = {};
  for (const field of fields) {
    if (field.kind === "table" || !(field.name in params)) continue;
    const raw = params[field.name];
    if (field.kind === "number") values[field.name] = raw === "" ? null : Number(raw);
    else if (field.kind === "boolean") values[field.name] = raw === "true";
    else if (field.kind === "list") values[field.name] = parseListText(raw, field.itemKind).values;
    else values[field.name] = raw;
  }
  return values;
}
