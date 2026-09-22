// Editable dimensions in the Sintesi sketch (owner's request, 2026-09-22: "caselle di input per
// modificare i parametri mostrati nei disegni"). A dimension whose text reads "<symbol> = <value>
// <unit>" and matches a NUMBER field of the Dati form by symbol AND unit becomes a button in the
// SVG (sketch-shapes.js buildDimension marks it with `data-campo`); activating it opens a small
// popover next to the dimension with one input. Applying writes the value into the form control
// and fires a native "input" event, so js/forms.js's own handleChange runs exactly as if the
// user had typed in the Dati column: validation, persistence, live recalculation, redraw.
// Pure matching (`campoPerTesto`) is exported for node tests; everything else needs the DOM.
import { el, clear } from "./dom.js";
import { symbolNode } from "./symbols.js";
import { parseDecimal } from "./number-input.js";

const QUOTA_RE = /^(.+?) = ([^ ]+)(?: (.+))?$/;
const REFOCUS_MS = 450; // after the live run has redrawn the sketch (debounce + render)
const FLASH_MS = 1600;

// "kN/m2" (field hint) and "kN/m²" (sketch text) are the same unit.
function unitKey(unit) {
  return (unit || "").replace(/²/g, "2").replace(/³/g, "3").trim();
}

// The shown number equals the field's current value, at the precision the text shows: the guard
// that keeps a RESULT label ("S_stat = 30 kN") from ever being linked to an input that happens to
// share its symbol and unit.
function shownValueMatches(shown, current) {
  const value = parseDecimal(shown);
  if (value === null || current === null || current === undefined) return false;
  const decimals = shown.includes(",") ? shown.length - shown.indexOf(",") - 1 : 0;
  return Math.abs(value - current) <= 0.5 * 10 ** -decimals + 1e-9;
}

// The number field a sketch text ("<symbol> = <value> <unit>") stands for, or null. Either the
// sketch names it (`campo`, wins as long as that field exists) or symbol AND unit match a field
// whose current value (`valoreDi(name)`) is the one shown.
export function campoPerTesto(testo, fields, { campo = null, valoreDi = null } = {}) {
  const numeric = (fields || []).filter((f) => f.kind === "number");
  if (campo) return numeric.find((f) => f.name === campo) || null;
  const match = QUOTA_RE.exec(testo || "");
  if (!match) return null;
  const [, symbol, shown, unit = ""] = match;
  const field = numeric.find((f) => f.symbol === symbol && unitKey(f.unit) === unitKey(unit));
  if (!field || !valoreDi) return null;
  return shownValueMatches(shown, valoreDi(field.name)) ? field : null;
}

// Current value of a Dati control, for the guard above (null when the form is not on the page).
export function valoreCampoCorrente(name) {
  const form = document.getElementById("tool-form");
  const control = form && form.elements.namedItem(name);
  return control ? parseDecimal(control.value) : null;
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
  const target = event.target.closest ? event.target.closest(".sk-modificabile[data-campo]") : null;
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
  // WORKBENCH_SPEC §23.5: "a 'Dimensiona' link in §18's sketch popover for the field being
  // edited" -- dynamic import, same reasoning as js/dimensiona.js's own "Studia la sensibilità"
  // button: this popover must not pull the whole search dialog graph in on every sketch click.
  const dimensiona = el("button", { type: "button", class: "sk-edit-dimensiona", text: "Dimensiona" });
  dimensiona.addEventListener("click", () => {
    closePopover(state);
    import("./dimensiona.js").then(({ openDimensiona }) => openDimensiona(field.name));
  });
  const popover = el("form", { class: "sk-edit", role: "dialog", "aria-label": `Modifica ${field.symbol || field.name}` }, [
    el("div", { class: "sk-edit-row" }, [label, input, unit]),
    error,
    el("div", { class: "sk-edit-actions" }, [apply, cancel, dimensiona]),
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
  // WORKBENCH_SPEC §21.1: "§18 sketch edits are ordinary steps" -- js/annulla-ui.js commits on
  // `change`, not `input` (which the app also still needs for validation/live run, unchanged).
  control.dispatchEvent(new Event("change", { bubbles: true }));
  const wrapper = document.querySelector(`.f-field[data-field="${field.name}"]`);
  if (!wrapper) return;
  wrapper.classList.add("f-field--flash");
  setTimeout(() => wrapper.classList.remove("f-field--flash"), FLASH_MS);
}

function refocus(name) {
  const next = document.querySelector(`#sintesi .sk-modificabile[data-campo="${name}"]`);
  if (next) next.focus();
}
