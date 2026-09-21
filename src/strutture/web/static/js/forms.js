// Builds the input form (sections, conditions, unit selector, actions) and self-wires to the
// shared `strutture:*` events: listens for `tool-schema`/`run-start`/`run-result`, emits
// `run-request`. Section/summary/unit-selector builders live in forms-sections.js; the
// run-result / run-network-error handling lives in forms-submit.js (imported below for its
// side effects -- it reads/writes the shared `current` state exported from this module).
import { el, clear } from "./dom.js";
import { describeFields } from "./schema.js";
import { buildField, setValue, setFieldError } from "./fields.js";
import { validateValues } from "./validate.js";
import { save, load, fromParams } from "./form-state.js";
import { groupFields, buildSection, visibleValues, applyConditions, wireUnitSelector, renderSummary, copyShareLink } from "./forms-sections.js";
import "./forms-submit.js";

const FORM_ID = "tool-form";

// `renderForm(root, {fields, example, initialValues}) -> FormApi`, per DESIGN_SPEC §5.
// `tool` is an extension of the sketch (needed for persistence/share-link); passed by our own
// `strutture:tool-schema` listener below, defaults to "" for direct/standalone callers.
export function renderForm(root, { fields = [], example = null, initialValues = {}, tool = "" } = {}) {
  clear(root);
  const actions = document.getElementById("form-actions");
  if (actions) clear(actions);

  const form = el("form", { id: FORM_ID, class: "f-form", novalidate: true, "aria-busy": "false" });
  const { sections, advanced } = groupFields(fields);
  for (const [name, sectionFields] of sections) form.append(buildSection(name, sectionFields));
  if (advanced.length > 0) {
    const details = el("details", { class: "f-section f-advanced" });
    details.append(el("summary", { text: "Avanzate" }));
    advanced.forEach((field) => details.append(buildField(field)));
    form.append(details);
  }
  root.append(form);

  fields.forEach((field) => setValue(form, field, initialValues[field.name] ?? field.default));
  applyConditions(form, fields);
  wireUnitSelector(form, fields);
  form.addEventListener("change", () => applyConditions(form, fields));

  const calcolaButton = el("button", { type: "submit", form: FORM_ID, class: "f-run-button", text: "Calcola" });
  const exampleButton = el("button", {
    type: "button",
    class: "f-example-button",
    text: "Carica esempio",
    hidden: example == null,
    onclick: () => {
      fields.forEach((field) => setValue(form, field, example ? example[field.name] : undefined));
      applyConditions(form, fields);
    },
  });
  const copyLinkButton = el("button", {
    type: "button",
    class: "f-copylink-button",
    text: "Copia link",
    onclick: () => copyShareLink(form, fields, tool, copyLinkButton),
  });
  // Order: "Carica esempio" before "Calcola" so a keyboard-only user can tab to the example
  // and fill the form with Enter before reaching the submit button (DESIGN_SPEC §7 test 3).
  if (actions) actions.append(exampleButton, calcolaButton, copyLinkButton);

  const api = {
    values: () => visibleValues(form, fields),
    setValues: (values) => {
      fields.forEach((field) => setValue(form, field, values[field.name]));
      applyConditions(form, fields);
    },
    setFieldErrors: (byField, general = []) => {
      fields.forEach((field) => setFieldError(form, field.name, byField[field.name] || null));
      renderSummary(fields, byField, general);
    },
    clearErrors: () => {
      fields.forEach((field) => setFieldError(form, field.name, null));
      renderSummary(fields, {}, []);
    },
    setBusy: (busy) => {
      form.setAttribute("aria-busy", String(busy));
      calcolaButton.disabled = busy;
      calcolaButton.textContent = busy ? "Calcolo…" : "Calcola";
    },
    applyConditions: () => applyConditions(form, fields),
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const values = visibleValues(form, fields);
    const errors = validateValues(fields, values);
    if (Object.keys(errors).length > 0) {
      api.setFieldErrors(errors);
      const firstInvalid = form.querySelector('[aria-invalid="true"]');
      if (firstInvalid) firstInvalid.focus();
      return;
    }
    api.clearErrors();
    save(tool, values, fields);
    document.dispatchEvent(new CustomEvent("strutture:run-request", { detail: { name: tool, values }, bubbles: true }));
  });

  return api;
}

// Self-wiring: rebuilds the form on every tool selection. Mutated in place (never reassigned)
// so forms-submit.js can hold a live reference to the same object.
export const current = { tool: null, fields: [], api: null };

document.addEventListener("strutture:tool-schema", (event) => {
  const { name, input, example, params } = event.detail;
  const root = document.getElementById("form-root");
  if (!root) return;
  const fields = describeFields(input || {});
  const defaults = Object.fromEntries(fields.filter((f) => f.default !== undefined).map((f) => [f.name, f.default]));
  const initialValues = { ...defaults, ...(load(name) || {}), ...fromParams(params || {}, fields) };
  current.tool = name;
  current.fields = fields;
  current.api = renderForm(root, { fields, example, initialValues, tool: name });
});
