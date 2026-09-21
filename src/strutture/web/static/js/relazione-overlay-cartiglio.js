// "Cartiglio" fieldset of the report personalisation overlay's Opzioni pane (WORKBENCH_SPEC §11):
// progetto, committente, elemento (default = tool title), relazione n., revisione, sigla, data
// (default today, editable), note. Built ONCE per overlay session (not rebuilt on every
// keystroke, unlike the Contenuto fieldset): text edits only update state + reschedule the
// preview, they never change any OTHER control's enabled state, so there is nothing to re-render.
import { el } from "./dom.js";
import { CARTIGLIO_FIELDS } from "./relazione-options.js";

function fieldControl(field, value, onChange) {
  const id = `rel-cartiglio-${field.key}`;
  const handler = (event) => onChange(field.key, event.target.value);
  if (field.kind === "textarea") {
    const textarea = el("textarea", { id, name: field.key, rows: "2" });
    textarea.value = value || "";
    textarea.addEventListener("input", handler);
    return textarea;
  }
  const input = el("input", { id, name: field.key, type: field.kind === "date" ? "date" : "text" });
  input.value = value || "";
  input.addEventListener("input", handler);
  return input;
}

// `values` = the RAW stored/edited cartiglio (before `effectiveCartiglio` defaults are applied --
// the field shows a placeholder for elemento/data, not a value the user never actually typed).
export function buildCartiglioFieldset(values, { toolTitle, todayIso, onChange }) {
  const fieldset = el("fieldset", { class: "rel-fieldset" }, [el("legend", { text: "Cartiglio" })]);
  for (const field of CARTIGLIO_FIELDS) {
    const row = el("div", { class: "rel-field-row" });
    row.append(el("label", { class: "rel-field-label", for: `rel-cartiglio-${field.key}`, text: field.label }));
    const control = fieldControl(field, values[field.key], onChange);
    if (field.key === "elemento") control.placeholder = toolTitle || "";
    if (field.key === "data") control.placeholder = todayIso;
    row.append(control);
    fieldset.append(row);
  }
  return fieldset;
}
