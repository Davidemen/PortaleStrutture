// Pure form-building helpers used by forms.js: section grouping, conditional visibility,
// the unit-selector wiring (§4b D1) and the error summary / share-link widgets. No event
// self-wiring lives here -- these all take the `form`/`fields` they act on as arguments.
// The accordion DOM itself (one-line summary + error badge + persisted open state) is built by
// form-sections-summary.js from the `sections` Map `groupFields` returns below.
import { el, clear } from "./dom.js";
import { fieldInputId, readValue } from "./fields.js";
import { isVisible } from "./validate.js";
import { toParams } from "./form-state.js";
import { refreshUnitHeaders } from "./table-input.js";
import { copyText, buildManualCopyField } from "./clipboard.js";

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

export function rawValues(form, fields) {
  const values = {};
  fields.forEach((field) => {
    values[field.name] = readValue(form, field);
  });
  return values;
}

// A field hidden by an unmet `condition` almost always maps to an Optional server-side field
// (default=None) for which omitting the key or sending its untouched empty value are the same
// thing -- but the schema hint is a UI display rule, not a guarantee the field is optional on the
// server (e.g. ca-punzonamento's `diametro_mm`: required, only USED when `lato_a_mm=0`, but still
// a required key on every request). Excluding a still-required-but-hidden field's key from the
// payload turned every rectangular-column request into a "campo obbligatorio mancante" server
// error the engineer could never see (the field is hidden). So every field's value is sent
// regardless of visibility; only an untouched, still-empty HIDDEN field falls back to its own
// `default` (identical to what the server already assumes) or -- lacking one -- its declared
// minimum/0, the most conservative value a `ge=0` numeric field can hold. A VISIBLE empty
// required field is untouched here (stays null) so `validateValues` still flags it normally.
function fallbackFor(field) {
  if (field.default !== undefined) return field.default;
  if (field.kind !== "number") return null;
  if (typeof field.minimum === "number") return field.minimum;
  if (typeof field.exclusiveMin === "number") return field.exclusiveMin + 1;
  return 0;
}

export function visibleValues(form, fields) {
  const raw = rawValues(form, fields);
  const values = {};
  fields.forEach((field) => {
    const value = raw[field.name];
    const visible = isVisible(field, raw);
    values[field.name] = visible || value !== null && value !== undefined ? value : fallbackFor(field);
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
        if (span) span.textContent = unit || "";
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

// Bug fix (2026-09-21): the app is reached over a VPN at http://<ip>:<port>, not a secure
// context, so `navigator.clipboard` is undefined there -- this used to show "Copiato"
// unconditionally in that case (and on a rejected write). `copyText()` never lies; a failed copy
// shows the link in a manual-copy field instead. Tables never make it into the link at all
// (`toParams` skips `field.kind === "table"`) -- say so next to the button when that applies.
function clearFeedback(button) {
  let node = button.nextElementSibling;
  while (node && (node.classList.contains("sm-clip-fallback") || node.classList.contains("sm-clip-note"))) {
    const next = node.nextElementSibling;
    node.remove();
    node = next;
  }
}

export async function copyShareLink(form, fields, tool, button) {
  const query = new URLSearchParams(toParams(visibleValues(form, fields), fields)).toString();
  const url = `${location.origin}${location.pathname}#/${tool}${query ? `?${query}` : ""}`;
  clearFeedback(button);
  const ok = await copyText(url);
  button.textContent = ok ? "Copiato" : "Copia link";
  if (ok) setTimeout(() => { button.textContent = "Copia link"; }, 2000);
  else button.insertAdjacentElement("afterend", buildManualCopyField(url, "Link da condividere"));
  if (fields.some((field) => field.kind === "table")) {
    button.insertAdjacentElement("afterend", el("p", { class: "sm-clip-note", text: "La tabella non è inclusa nel link." }));
  }
}
