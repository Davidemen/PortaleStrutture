// PURE state module for the report personalisation overlay (WORKBENCH_SPEC §11): defaults, the
// three presets (Completa/Sintetica/Personalizzata), persistence (`sm.cartiglio`, per browser;
// `sm.relazione.<tool>`, per tool) and the cartiglio field metadata the overlay's form + the
// printed cartiglio (js/print.js) both read from. No DOM here -- `relazione-overlay*.js` own the
// UI, this module only ever returns/reads plain data. Reuses `resolveOptions`/`omittedSections`
// from js/relazione.js (already the §11 contract's one source of truth for "what is complete")
// rather than re-deriving them.
import { readJSON, writeJSON } from "./storage.js";
import { resolveOptions, omittedSections, DEFAULT_OPTIONS } from "./relazione.js";

export { resolveOptions, omittedSections, DEFAULT_OPTIONS };

export const CARTIGLIO_KEY = "sm.cartiglio";

// `elemento`/`data` are computed defaults (tool title / today), never stored as such -- an empty
// string in storage means "use the default", so switching tools or crossing midnight still shows
// the right default instead of a stale typed-then-cleared value.
export const CARTIGLIO_FIELDS = [
  { key: "progetto", label: "Progetto", kind: "text" },
  { key: "committente", label: "Committente", kind: "text" },
  { key: "elemento", label: "Elemento", kind: "text" },
  { key: "relazioneN", label: "Relazione n.", kind: "text" },
  { key: "revisione", label: "Revisione", kind: "text" },
  { key: "sigla", label: "Sigla", kind: "text" },
  { key: "data", label: "Data", kind: "date" },
  { key: "note", label: "Note", kind: "textarea" },
];

export function cartiglioFields() {
  return readJSON(CARTIGLIO_KEY, {});
}

export function saveCartiglio(next) {
  writeJSON(CARTIGLIO_KEY, next);
}

function todayIso() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

export function formatIsoDateIt(iso) {
  if (!iso) return "";
  const [y, m, d] = iso.split("-");
  return y && m && d ? `${d}/${m}/${y}` : iso;
}

// "elemento (default = tool title)", "data (default today, editable)" (WORKBENCH_SPEC §11) --
// applied only at READ time (preview/print/form prefill), never written back to storage.
export function effectiveCartiglio(raw, toolTitle) {
  const source = raw || {};
  return {
    ...source,
    elemento: source.elemento || toolTitle || "",
    data: source.data || todayIso(),
  };
}

export function contentsKey(toolName) {
  return `sm.relazione.${toolName}`;
}

export function loadContents(toolName) {
  return readJSON(contentsKey(toolName), null);
}

export function saveContents(toolName, options) {
  writeJSON(contentsKey(toolName), options);
}

export const PRESET_COMPLETA = "completa";
export const PRESET_SINTETICA = "sintetica";
export const PRESET_PERSONALIZZATA = "personalizzata";

// Top-level output-schema "group" nodes only (WORKBENCH_SPEC §11: "Risultati: one checkbox per
// result group of the CURRENT tool taken from the output schema") -- row tables get their own
// "Tabelle" toggle, nested subgroups fold under their parent's own section (js/relazione-groups.js
// `buildGroupsSection` only ever gates TOP-LEVEL nodes on `sezioni.gruppi`).
export function resultGroups(outputNodes) {
  return (outputNodes || []).filter((node) => node.kind === "group").map((node) => ({ path: node.path, label: node.label }));
}

function sintesiSezioni(outputNodes) {
  return {
    passaggi: false,
    tabelle: false,
    grafici: false,
    avvisi: false,
    nota_correzioni: false,
    gruppi: Object.fromEntries(resultGroups(outputNodes).map((g) => [g.path, false])),
  };
}

// Applies a preset to `current` (a resolved options object): Completa/Sintetica RESET `sezioni`
// to that preset's canonical set (never a merge -- picking a preset after custom edits must give
// the preset's own values back, WORKBENCH_SPEC §11), Personalizzata just unlocks the current
// values. `tabelle`/`pagina` (row policy, page layout) are untouched: presets are about CONTENT.
export function applyPreset(preset, current, outputNodes) {
  if (preset === PRESET_SINTETICA) {
    return resolveOptions({ ...current, preset, sezioni: sintesiSezioni(outputNodes) });
  }
  if (preset === PRESET_PERSONALIZZATA) {
    return resolveOptions({ ...current, preset });
  }
  return resolveOptions({ ...current, preset: PRESET_COMPLETA, sezioni: {} });
}

// Any Contenuto edit (WORKBENCH_SPEC §11 "changing any checkbox switches the preset to
// Personalizzata") goes through here: `patch` is a partial `sezioni` object to merge in.
export function editSezioni(current, patch) {
  return resolveOptions({ ...current, preset: PRESET_PERSONALIZZATA, sezioni: { ...current.sezioni, ...patch } });
}

export function editGruppo(current, path, included) {
  return editSezioni(current, { gruppi: { ...current.sezioni.gruppi, [path]: included } });
}

// Schizzo/Dati di ingresso can only be unticked in Personalizzata (WORKBENCH_SPEC §11) -- both
// presets other than Personalizzata force them on, so the overlay disables those two checkboxes
// rather than letting an edit silently no-op.
export function sectionLocked(resolved) {
  return resolved.preset !== PRESET_PERSONALIZZATA;
}

export function editTabelle(current, patch) {
  return resolveOptions({ ...current, tabelle: { ...current.tabelle, ...patch } });
}

export function editPagina(current, patch) {
  return resolveOptions({ ...current, pagina: { ...current.pagina, ...patch } });
}
