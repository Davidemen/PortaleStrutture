// Jump from a warning to the input it is about: open the field's accordion section (and the
// "Avanzate" disclosure when it lives there), scroll it into view, focus its control and flash it.
// An "avviso" that names one parameter is a link to that parameter (user request, 2026-09-22).
import { fieldInputId } from "./fields.js";

const FLASH_MS = 1600;
const MIN_SYMBOL_LENGTH = 2; // "D" alone would match half the Italian text

export function jumpToField(name) {
  const wrapper = document.querySelector(`.f-field[data-field="${name}"]`);
  if (!wrapper) return false;
  const section = wrapper.closest(".f-section");
  const toggle = section ? section.querySelector(".f-section-toggle") : null;
  if (toggle && toggle.getAttribute("aria-expanded") !== "true") toggle.click();
  const disclosure = wrapper.closest("details");
  if (disclosure && !disclosure.open) disclosure.open = true;
  wrapper.scrollIntoView({ block: "center" });
  const control = document.getElementById(fieldInputId(name)) || wrapper.querySelector("input, select, textarea");
  if (control) control.focus({ preventScroll: true });
  wrapper.classList.add("f-field--flash");
  setTimeout(() => wrapper.classList.remove("f-field--flash"), FLASH_MS);
  return true;
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// The input a warning is about: the report's own `avvisi_campi` first (the tool knows), otherwise
// the first field whose symbol appears as a whole word in the text ("V_g", "T_R"); null when none.
export function fieldForWarning(text, avvisiCampi, fields) {
  if (avvisiCampi && avvisiCampi[text]) return avvisiCampi[text];
  for (const field of fields || []) {
    const symbol = field.symbol;
    if (!symbol || symbol.length < MIN_SYMBOL_LENGTH) continue;
    if (new RegExp(`(^|[^\\p{L}\\p{N}_])${escapeRegExp(symbol)}(?![\\p{L}\\p{N}])`, "u").test(text)) return field.name;
  }
  return null;
}
