// Numeric field control -- WORKBENCH_SPEC §3. A text input (`inputmode="decimal"`) rather than
// `type="number"`: some browsers reject a typed Italian decimal comma in a native number input.
// Accepts "," and "." as the decimal separator, right-aligns (css/forms.css `.f-number`),
// select-all on focus, and Up/Down arrow stepping (Shift x10) -- while still submitting a plain
// JS number (`readValue` in fields.js calls `parseDecimal` on the way out).
import { el } from "./dom.js";

// "1,5" / "1.5" -> 1.5; "1.234,56" (thousands + decimal) -> 1234.56: every "." but the last one
// is treated as a thousands separator once a "," has been normalised to ".". Empty/garbage -> null.
export function parseDecimal(text) {
  if (text === null || text === undefined) return null;
  const trimmed = String(text).trim();
  if (trimmed === "") return null;
  let normalized = trimmed.replace(/,/g, ".");
  const lastDot = normalized.lastIndexOf(".");
  const dotCount = (normalized.match(/\./g) || []).length;
  if (dotCount > 1) {
    normalized = `${normalized.slice(0, lastDot).replace(/\./g, "")}${normalized.slice(lastDot)}`;
  }
  const value = Number(normalized);
  return Number.isFinite(value) ? value : null;
}

// Display form for a parsed number (or the raw text already in the field): it-IT decimal comma.
export function formatForInput(value) {
  if (value === null || value === undefined || value === "") return "";
  return String(value).replace(".", ",");
}

function stepOf(field) {
  const raw = Number(field.step);
  return Number.isFinite(raw) && raw > 0 ? raw : 1;
}

function clamp(value, field) {
  let next = value;
  if (field.minimum != null) next = Math.max(next, field.minimum);
  if (field.maximum != null) next = Math.min(next, field.maximum);
  return next;
}

// Keeps repeated Up/Down presses from drifting on float error (0.1 + 0.2 style accumulation).
function roundToStep(value, step) {
  const decimals = (String(step).split(".")[1] || "").length;
  const factor = 10 ** Math.min(decimals, 8);
  return Math.round(value * factor) / factor;
}

function applyStep(input, field, direction, shiftKey) {
  const step = stepOf(field) * (shiftKey ? 10 : 1);
  const current = parseDecimal(input.value) ?? 0;
  const next = clamp(roundToStep(current + direction * step, stepOf(field)), field);
  input.value = formatForInput(next);
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

export function buildNumberInput(field, id, describedById) {
  const input = el("input", {
    type: "text",
    id,
    name: field.name,
    class: "f-number",
    inputmode: "decimal",
    value: formatForInput(field.default),
    required: field.required,
    "aria-describedby": describedById,
  });
  input.addEventListener("focus", () => input.select());
  input.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
    event.preventDefault();
    applyStep(input, field, event.key === "ArrowUp" ? 1 : -1, event.shiftKey);
  });
  return input;
}
