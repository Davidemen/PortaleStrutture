// Pure form-building helpers used by forms.js: section grouping, conditional visibility,
// the unit-selector wiring (§4b D1) and the error summary / share-link widgets. No event
// self-wiring lives here -- these all take the `form`/`fields` they act on as arguments.
import { el, clear } from "./dom.js";
import { buildField, fieldInputId, readValue } from "./fields.js";
import { isVisible } from "./validate.js";
import { toParams } from "./form-state.js";
import { refreshUnitHeaders } from "./table-input.js";

export function groupFields(fields) {
  const sections = new Map();
  const advanced = [];
  for (const field of fields) {
    if (field.advanced) {
      advanced.push(field);
      continue;
    }
    const key = field.group || "";
    if (!sections.has(key)) sections.set(key, []);
    sections.get(key).push(field);
  }
  return { sections, advanced };
}

export function buildSection(name, sectionFields) {
  const section = el("section", { class: "f-section" });
  if (name) section.append(el("h3", { text: name }));
  sectionFields.forEach((field) => section.append(buildField(field)));
  return section;
}

export function rawValues(form, fields) {
  const values = {};
  fields.forEach((field) => {
    values[field.name] = readValue(form, field);
  });
  return values;
}

export function visibleValues(form, fields) {
  const raw = rawValues(form, fields);
  const values = {};
  fields.forEach((field) => {
    if (isVisible(field, raw)) values[field.name] = raw[field.name];
  });
  return values;
}

export function applyConditions(form, fields) {
  const raw = rawValues(form, fields);
  fields.forEach((field) => {
    if (!field.condition) return;
    const wrapper = form.querySelector(`.f-field[data-field="${field.name}"]`);
    if (wrapper) wrapper.hidden = !isVisible(field, raw);
  });
}

function hasUnitOptions(field) {
  return Boolean(field.unitOptions) || (field.kind === "table" && (field.columns || []).some((c) => c.unitOptions));
}

export function wireUnitSelector(form, fields) {
  const selector = fields.find((field) => field.unitSelector);
  const dependents = fields.filter(hasUnitOptions);
  if (!selector || dependents.length === 0) return;
  const control = form.elements.namedItem(selector.name);
  if (!control) return;
  const apply = () => {
    const key = control.value;
    dependents.forEach((field) => {
      const wrapper = form.querySelector(`.f-field[data-field="${field.name}"]`);
      if (!wrapper) return;
      if (field.kind === "table") {
        const container = wrapper.querySelector(".f-table");
        if (container) refreshUnitHeaders(container, key);
      } else {
        const unit = (field.unitOptions && field.unitOptions[key]) || field.unit;
        const span = wrapper.querySelector(".f-unit");
        if (span) span.textContent = unit ? `[${unit}]` : "";
      }
    });
  };
  control.addEventListener("change", apply);
  apply();
}

export function renderSummary(fields, byField, general) {
  const summary = document.getElementById("error-summary");
  if (!summary) return;
  clear(summary);
  const entries = Object.entries(byField);
  if (entries.length === 0 && general.length === 0) {
    summary.hidden = true;
    return;
  }
  summary.hidden = false;
  if (entries.length > 0) summary.append(el("p", { text: `${entries.length} campi da correggere` }));
  const list = el("ul");
  entries.forEach(([name, message]) => {
    const field = fields.find((f) => f.name === name);
    list.append(el("li", {}, [el("a", { href: `#${fieldInputId(name)}`, text: `${field ? field.label : name}: ${message}` })]));
  });
  general.forEach((message) => list.append(el("li", { text: message })));
  summary.append(list);
}

export function copyShareLink(form, fields, tool, button) {
  const query = new URLSearchParams(toParams(visibleValues(form, fields), fields)).toString();
  const url = `${location.origin}${location.pathname}#/${tool}${query ? `?${query}` : ""}`;
  const restore = () => {
    button.textContent = "Copia link";
  };
  const confirmCopy = () => {
    button.textContent = "Copiato";
    setTimeout(restore, 2000);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(confirmCopy, confirmCopy);
  } else {
    confirmCopy();
  }
}
