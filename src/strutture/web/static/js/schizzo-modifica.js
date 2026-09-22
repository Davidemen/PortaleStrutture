// Editable dimensions in the Sintesi sketch (owner's request, 2026-09-22: "caselle di input per
// modificare i parametri mostrati nei disegni"). A dimension whose text reads "<symbol> = <value>
// <unit>" and matches a NUMBER field of the Dati form by symbol AND unit becomes a button in the
// SVG (sketch-shapes.js buildDimension marks it with `data-campo`); activating it opens a small
// popover next to the dimension with one input. Applying writes the value into the form control
// and fires a native "input" event, so js/forms.js's own handleChange runs exactly as if the
// user had typed in the Dati column: validation, persistence, live recalculation, redraw.
// Pure matching (`campoPerQuota`) is exported for node tests; everything else needs the DOM.
import { el, clear } from "./dom.js";
import { symbolNode } from "./symbols.js";

const QUOTA_RE = /^(.+?) = ([^ ]+)(?: (.+))?$/;
const REFOCUS_MS = 450; // after the live run has redrawn the sketch (debounce + render)
const FLASH_MS = 1600;

// The number field a dimension text stands for, or null. Symbol and unit must both match the
// field's own (unit "" for dimensionless); the shown value is never compared (a compressed
// drawing still prints the true value, a rounded text would not equal the input anyway).
export function campoPerQuota(testo, fields, campo = null) {
  const numeric = (fields || []).filter((f) => f.kind === "number");
  if (campo) return numeric.find((f) => f.name === campo) || null; // the sketch names the field itself
  const match = QUOTA_RE.exec(testo || "");
  if (!match) return null;
  const [, symbol, , unit = ""] = match;
  return numeric.find((f) => f.symbol === symbol && (f.unit || "") === unit) || null;
}

const editors = new WeakMap(); // root -> { fields, popover }

export function mountSketchEditing(root, { fields = [] } = {}) {
  if (!root) return;
  const state = editors.get(root) || { fields, popover: null };
  state.fields = fields;
  if (!editors.has(root)) {
    editors.set(root, state);
    root.addEventListener("click", (event) => activate(event, root, state));
    root.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") activate(event, root, state);
    });
  }
}

function activate(event, root, state) {
  const target = event.target.closest ? event.target.closest(".sk-quota-text[data-campo]") : null;
  if (!target || !root.contains(target)) return;
  event.preventDefault();
  const field = state.fields.find((f) => f.name === target.dataset.campo);
  const form = document.getElementById("tool-form");
  const control = form && form.elements.namedItem(field ? field.name : "");
  if (!field || !control) return;
  openPopover(state, target, field, control);
}

function openPopover(state, anchor, field, control) {
  closePopover(state);
  const input = el("input", {
    type: "text", inputmode: "decimal", class: "sk-edit-input", value: control.value,
    id: "sk-edit-input", autocomplete: "off",
  });
  const label = el("label", { class: "sk-edit-label", for: "sk-edit-input" }, [symbolNode(field.symbol || field.name)]);
  const unit = el("span", { class: "sk-edit-unit", text: field.unit || "" });
  const error = el("p", { class: "sk-edit-error", hidden: true });
  const apply = el("button", { type: "submit", class: "sk-edit-apply", text: "Applica" });
  const cancel = el("button", { type: "button", class: "sk-edit-cancel", text: "Annulla" });
  const popover = el("form", { class: "sk-edit", role: "dialog", "aria-label": `Modifica ${field.symbol || field.name}` }, [
    el("div", { class: "sk-edit-row" }, [label, input, unit]),
    error,
    el("div", { class: "sk-edit-actions" }, [apply, cancel]),
  ]);
  popover.addEventListener("submit", (event) => {
    event.preventDefault();
    const raw = input.value.trim();
    if (raw === "" || Number.isNaN(Number(raw.replace(",", ".")))) {
      error.hidden = false;
      error.textContent = "Inserire un numero";
      input.focus();
      return;
    }
    applyValue(control, field, raw);
    closePopover(state);
    setTimeout(() => refocus(field.name), REFOCUS_MS);
  });
  cancel.addEventListener("click", () => {
    closePopover(state);
    anchor.focus();
  });
  popover.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closePopover(state);
      anchor.focus();
    }
  });
  document.body.append(popover);
  place(popover, anchor);
  state.popover = popover;
  state.onOutside = (event) => {
    if (!popover.contains(event.target) && event.target !== anchor && !anchor.contains(event.target)) closePopover(state);
  };
  setTimeout(() => document.addEventListener("pointerdown", state.onOutside), 0);
  input.focus();
  input.select();
}

function closePopover(state) {
  if (state.onOutside) document.removeEventListener("pointerdown", state.onOutside);
  state.onOutside = null;
  if (state.popover) {
    clear(state.popover);
    state.popover.remove();
  }
  state.popover = null;
}

function place(popover, anchor) {
  const rect = anchor.getBoundingClientRect();
  const width = popover.offsetWidth || 260;
  const height = popover.offsetHeight || 110;
  const left = Math.max(8, Math.min(rect.left, window.innerWidth - width - 8));
  const below = rect.bottom + 6;
  const top = below + height > window.innerHeight - 8 ? Math.max(8, rect.top - height - 6) : below;
  popover.style.setProperty("left", `${Math.round(left)}px`);
  popover.style.setProperty("top", `${Math.round(top)}px`);
}

function applyValue(control, field, raw) {
  control.value = raw;
  control.dispatchEvent(new Event("input", { bubbles: true }));
  const wrapper = document.querySelector(`.f-field[data-field="${field.name}"]`);
  if (!wrapper) return;
  wrapper.classList.add("f-field--flash");
  setTimeout(() => wrapper.classList.remove("f-field--flash"), FLASH_MS);
}

function refocus(name) {
  const next = document.querySelector(`#sintesi .sk-quota-text[data-campo="${name}"]`);
  if (next) next.focus();
}
