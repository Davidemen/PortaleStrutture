// The "cartiglio" (title block) every printed report opens with -- WORKBENCH_SPEC §10/§11. Field
// EDITING lives in the report personalisation overlay's options pane (js/relazione-overlay-
// cartiglio.js); persistence (`sm.cartiglio`) and the field defaults (elemento/data) live in
// js/relazione-options.js, the ONE owner of that storage key -- this module only ever reads them
// and prints plain text (nothing in a printed report is interactive, so no `<input>` here).
// `js/relazione.js` is the module that actually composes the printed document; this one only
// owns the cartiglio piece of it. `overrides`, when given (the overlay's live, not-yet-saved
// edits), win over storage -- WORKBENCH_SPEC §11's `options.cartiglio` contract.
import { el } from "./dom.js";
import { cartiglioFields, effectiveCartiglio, formatIsoDateIt, CARTIGLIO_FIELDS } from "./relazione-options.js";

const LABELS = Object.fromEntries(CARTIGLIO_FIELDS.map((field) => [field.key, field.label]));

export function buildCartiglio(tool, mode, overrides = {}) {
  const current = effectiveCartiglio({ ...cartiglioFields(), ...overrides }, tool && tool.title);
  const section = el("section", { class: "print-cartiglio" });
  const meta = el("dl", { class: "print-cartiglio-meta" });
  const entries = [
    [LABELS.progetto, current.progetto],
    [LABELS.committente, current.committente],
    [LABELS.elemento, current.elemento],
    [LABELS.relazioneN, current.relazioneN],
    [LABELS.revisione, current.revisione],
    [LABELS.sigla, current.sigla],
    [LABELS.data, formatIsoDateIt(current.data)],
    ["Norma", (tool && tool.norm) || ""],
    ["Modalità", mode || "standard"],
  ];
  for (const [term, value] of entries) {
    if (!value) continue;
    meta.append(el("dt", { text: term }));
    meta.append(el("dd", { text: value }));
  }
  section.append(meta);
  if (current.note) section.append(el("p", { class: "print-cartiglio-note", text: current.note }));
  return section;
}
