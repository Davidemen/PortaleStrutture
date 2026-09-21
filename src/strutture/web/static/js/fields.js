// Builds one `.f-field` (label + control + help + error) from a Field descriptor (schema.js).
// WORKBENCH_SPEC finding A: at >=380px of the Dati column's own width (forms.css container query
// on `.f-form`) each field is ONE row -- symbol + description on the left (clamped to 2 lines,
// full text in `title` + a "?" disclosure for anything that would not fit), the control on the
// right with its unit as a suffix INSIDE the control rather than in the label. Below 380px (or for
// table/boolean fields, which never use the row grid) it falls back to the original label-above-
// control stack.
import { el } from "./dom.js";
import { buildComuneInput } from "./comune-widget.js";
import { buildTableField, readTableValue, setTableValue } from "./table-input.js";
import { symbolNode } from "./symbols.js";
import { buildNumberInput, parseDecimal, formatForInput } from "./number-input.js";
import { formatUnit } from "./format.js";
import { buildListField, readListValue, setListValue } from "./list-input.js";

// A description this long will not fit the 2-line clamp at a ~150-200px-narrower compact row
// (the control column takes the rest) -- past this length a "?" disclosure reveals the full text
// instead of letting it silently clip.
const LONG_LABEL_CHARS = 64;

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
  const label = el("label", { for: id, class: "f-field-label" });
  if (field.symbol) label.append(symbolNode(field.symbol));
  label.append(el("span", { class: "f-field-desc", text: field.label, title: field.label }));
  return label;
}

// The "?" disclosure (WORKBENCH_SPEC finding A): toggles a full-width paragraph with the
// untruncated description below the row. Returns null for a description short enough that the
// 2-line clamp alone already shows it in full.
function buildLongDescriptor(field, descId) {
  if (!field.label || field.label.length <= LONG_LABEL_CHARS) return null;
  const full = el("p", { class: "f-field-full", id: descId, hidden: true, text: field.label });
  const toggle = el("button", {
    type: "button",
    class: "f-field-more",
    "aria-expanded": "false",
    "aria-controls": descId,
    "aria-label": `Mostra la descrizione completa: ${field.label}`,
    text: "?",
  });
  toggle.addEventListener("click", () => {
    const open = toggle.getAttribute("aria-expanded") !== "true";
    toggle.setAttribute("aria-expanded", String(open));
    full.hidden = !open;
  });
  return { toggle, full };
}

// The widest unit string this field can ever show, INCLUDING every `unit_options` alternative
// (the unit selector, forms-sections.js `wireUnitSelector`, can swap it after first paint) -- the
// reserved padding below sizes itself off this, not a fixed guess, so "kN/m3"/"kN/m2" get as much
// room as "m"/"°"/"-" without wasting space on the short, common case.
function widestUnit(field) {
  const options = field.unitOptions ? Object.values(field.unitOptions) : [];
  const candidates = [field.unit, ...options].filter(Boolean);
  return candidates.reduce((max, text) => Math.max(max, text.length), 1);
}

// Unit AS A SUFFIX INSIDE the control (finding A), not in the label: a plain sibling `<span>`
// positioned over the control's own padding by CSS. `wireUnitSelector` (forms-sections.js) still
// finds it by its stable `.f-unit` class regardless of where it now lives in the DOM. The reserved
// padding-right (forms.css, keyed off `--unit-chars`) is set here per field rather than as one
// fixed value for every unit -- a short "m"/"°"/"-" and a longer "kN/m3"/"kN/m2" both need the
// VALUE text to stop clear of the unit, and a single fixed padding sized for the short case left
// the two overlapping for the long one (measured on muro-sostegno's own soil unit weights).
function wrapControl(field, control, unitId) {
  // The list-input widget (js/list-input.js) shows its own unit text next to its chips row --
  // the absolute-positioned suffix below assumes a single-line control the same height as the
  // unit label, which a two-row (text + chips) widget is not.
  if (field.kind === "list") return control;
  if (!field.unit && !field.unitOptions) return control;
  const suffix = el("span", { class: "f-unit", id: unitId, "aria-hidden": "true", text: formatUnit(field.unit) || "" });
  const wrap = el("div", { class: "f-control-suffix" }, [control, suffix]);
  wrap.style.setProperty("--unit-chars", String(widestUnit(field)));
  return wrap;
}

function describedBy(helpId, errId, unitId) {
  return [helpId, errId, unitId].filter(Boolean).join(" ");
}

function buildControl(field, id, describedById, showTableMessage, unitId) {
  if (field.kind === "table") return buildTableField(field, id, { onMessage: showTableMessage });
  if (field.kind === "list") return buildListField(field, id, describedById, unitId);
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
  if (field.kind === "number") return buildNumberInput(field, id, describedById);
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
  const unitId = field.unit || field.unitOptions ? `${id}-unit` : null;
  const control = buildControl(field, id, describedBy(helpId, errId, unitId), showTableMessage, unitId);

  const wrapper = el("div", { class: "f-field", "data-field": field.name, "data-kind": field.kind });

  if (field.kind === "boolean") {
    wrapper.classList.add("f-field-checkbox");
    wrapper.append(el("div", { class: "f-field-row" }, [control, buildLabel(field, id)]));
  } else if (field.kind === "table") {
    wrapper.append(el("div", { class: "f-field-row" }, [buildLabel(field, id), control]));
  } else {
    const descId = `${id}-full`;
    const long = buildLongDescriptor(field, descId);
    const labelCell = el("div", { class: "f-field-labelcell" }, long ? [buildLabel(field, id), long.toggle] : [buildLabel(field, id)]);
    const controlWrap = el("div", { class: "f-field-control" }, [wrapControl(field, control, unitId)]);
    wrapper.append(el("div", { class: "f-field-row" }, [labelCell, controlWrap]));
    if (long) wrapper.append(long.full);
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
  if (field.kind === "list") return readListValue(form, field);
  const input = form.elements.namedItem(field.name);
  if (!input) return undefined;
  if (field.kind === "boolean") return input.checked;
  if (field.kind === "number") {
    const raw = input.value.trim();
    if (raw === "") return null;
    const parsed = parseDecimal(raw);
    // Keep the unparseable text (instead of null) so validate.js can flag it as "not a number"
    // rather than silently treating garbage input as an empty, valid-by-omission field.
    return parsed === null ? raw : parsed;
  }
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
  if (field.kind === "list") {
    setListValue(form, field, value);
    return;
  }
  const input = form.elements.namedItem(field.name);
  if (!input) return;
  if (field.kind === "boolean") input.checked = Boolean(value);
  else if (field.kind === "number") input.value = formatForInput(value);
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
