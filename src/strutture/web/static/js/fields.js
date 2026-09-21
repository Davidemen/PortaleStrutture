// Builds one `.f-field` (label + control + help + error) from a Field descriptor (schema.js).
import { el } from "./dom.js";
import { buildComuneInput } from "./comune-widget.js";
import { buildTableField, readTableValue, setTableValue } from "./table-input.js";
import { symbolNode } from "./symbols.js";

export function fieldInputId(name) {
  return `field-${name}`;
}

function errorId(name) {
  return `${fieldInputId(name)}-error`;
}

function allowsEmptyChoice(field) {
  return field.nullable || (!field.required && field.default === undefined);
}

function buildLabel(field, id) {
  const label = el("label", { for: id });
  if (field.symbol) label.append(symbolNode(field.symbol));
  label.append(document.createTextNode(field.symbol ? ` ${field.label}` : field.label));
  // Render the span even for `unit_options`-only fields (no static `unit`): forms.js's
  // `wireUnitSelector` fills in the right text right after build, per DESIGN_SPEC §4b D1.
  if (field.unit || field.unitOptions) {
    label.append(el("span", { class: "f-unit", text: field.unit ? `[${field.unit}]` : "" }));
  }
  return label;
}

function describedBy(helpId, errId) {
  return `${helpId} ${errId}`;
}

function buildControl(field, id, describedById, showTableMessage) {
  if (field.kind === "table") return buildTableField(field, id, { onMessage: showTableMessage });
  if (field.kind === "boolean") {
    return el("input", {
      type: "checkbox",
      id,
      name: field.name,
      checked: Boolean(field.default),
      "aria-describedby": describedById,
    });
  }
  if (field.widget === "comune") return buildComuneInput(field, id, describedById);
  if (field.kind === "enum") {
    const select = el("select", { id, name: field.name, required: field.required, "aria-describedby": describedById });
    if (allowsEmptyChoice(field)) {
      select.append(el("option", { value: "", text: "—", selected: field.default == null }));
    }
    for (const value of field.enumValues || []) {
      select.append(el("option", { value, text: String(value), selected: field.default === value }));
    }
    return select;
  }
  if (field.kind === "number") {
    return el("input", {
      type: "number",
      id,
      name: field.name,
      inputmode: "decimal",
      step: field.step,
      min: field.minimum,
      max: field.maximum,
      value: field.default ?? "",
      required: field.required,
      "aria-describedby": describedById,
    });
  }
  return el("input", {
    type: "text",
    id,
    name: field.name,
    value: field.default ?? "",
    required: field.required,
    "aria-describedby": describedById,
  });
}

export function buildField(field) {
  const id = fieldInputId(field.name);
  const helpId = `${id}-help`;
  const errId = errorId(field.name);
  const help = el("p", { class: "f-help", id: helpId, text: field.help || "" });
  // No `role="alert"` here: DESIGN_SPEC §3 fixes exactly 3 live regions app-wide (the shared
  // `#error-summary`/`#run-error` alerts + `#results-pane`'s polite region) -- a per-field alert
  // for every rendered field would multiply that count and spam screen readers on each render.
  // The message still reaches AT users via `aria-describedby` + `aria-invalid` on the control.
  const error = el("p", { class: "f-error", id: errId, hidden: true });
  const showTableMessage = (message) => {
    error.textContent = message || "";
    error.hidden = !message;
  };
  const control = buildControl(field, id, describedBy(helpId, errId), showTableMessage);

  const wrapper = el("div", { class: "f-field", "data-field": field.name, "data-kind": field.kind });
  if (field.kind === "boolean") {
    wrapper.classList.add("f-field-checkbox");
    wrapper.append(control, buildLabel(field, id));
  } else {
    wrapper.append(buildLabel(field, id), control);
  }
  wrapper.append(help, error);
  if (!field.help) help.hidden = true;
  return wrapper;
}

export function readValue(form, field) {
  if (field.kind === "table") {
    const container = form.querySelector(`[data-field="${field.name}"].f-table`);
    return container ? readTableValue(container) : [];
  }
  const input = form.elements.namedItem(field.name);
  if (!input) return undefined;
  if (field.kind === "boolean") return input.checked;
  if (field.kind === "number") return input.value === "" ? null : Number(input.value);
  if (field.kind === "enum") {
    const chosen = (field.enumValues || []).find((value) => String(value) === input.value);
    return chosen === undefined ? null : chosen;
  }
  const text = input.value.trim();
  return text === "" ? null : text;
}

// Programmatic fill (example load, restored inputs / hash params). `undefined` means "nothing
// to apply, leave the control as built" (its schema default) -- only `null`/a real value writes.
export function setValue(form, field, value) {
  if (value === undefined) return;
  if (field.kind === "table") {
    const container = form.querySelector(`[data-field="${field.name}"].f-table`);
    if (container) setTableValue(container, value);
    return;
  }
  const input = form.elements.namedItem(field.name);
  if (!input) return;
  if (field.kind === "boolean") input.checked = Boolean(value);
  else input.value = value ?? "";
}

export function setFieldError(form, name, message) {
  const field = form.querySelector(`.f-field[data-field="${name}"]`);
  if (!field) return;
  const error = field.querySelector(".f-error");
  if (error) {
    error.textContent = message || "";
    error.hidden = !message;
  }
  const control = form.elements.namedItem(name) || field.querySelector(".f-table");
  if (control) control.setAttribute("aria-invalid", message ? "true" : "false");
}
