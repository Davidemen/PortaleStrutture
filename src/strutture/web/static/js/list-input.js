// Generic widget for a JSON-schema `type: array` field whose `items` are scalars (number/string),
// not objects -- design review 2026-09-21, "acciaio-resistenza-incendio cannot run from the UI":
// the generic form had no input for a list of numbers (`table-input.js` only ever handles an array
// of OBJECTS, `schema.js isTableProperty`), so a field like `tempi_min` fell back to a single plain
// text input and sent a raw string where the backend needed a tuple of floats.
//
// One text field, values separated by comma/semicolon/space/newline, decimal comma accepted for
// numbers ("5; 10; 15,5" -> [5, 10, 15.5]); a live chip preview of the parsed values underneath;
// minItems/maxItems and per-item min/max validated with Italian messages. The parse/format/
// validate functions below are pure (no DOM) -- unit-tested directly with `node --test`
// (tests/e2e/list_input_parse.test.mjs); the widget builder at the bottom is the only DOM code.
import { el, clear } from "./dom.js";

// Semicolon and whitespace/newline are UNAMBIGUOUS separators; comma is not -- it is also the
// decimal separator ("15,5" must stay one token, not split into "15" and "5"). Split on the
// unambiguous ones first, then decide comma-by-chunk: exactly one comma inside an otherwise-
// unseparated chunk reads as a decimal point ("15,5" -> 15.5); a chunk with more than one comma
// cannot all be decimals, so every comma in it is a plain item separator instead ("5,10,15" ->
// three items). String items have no decimal concept -- every comma always separates.
const HARD_SEPARATOR_RE = /[;\s]+/;

function splitToken(chunk, itemKind) {
  const commaCount = (chunk.match(/,/g) || []).length;
  if (itemKind !== "string" && commaCount === 1) return [chunk];
  return chunk.split(",").map((piece) => piece.trim()).filter((piece) => piece.length > 0);
}

// {values, invalidTokens}: numeric items that fail to parse are reported separately rather than
// silently dropped, so the caller can flag them instead of quietly accepting a shorter list than
// the engineer typed. String items never fail to parse (any non-empty token is a valid string).
export function parseListText(text, itemKind = "number") {
  const chunks = String(text || "")
    .split(HARD_SEPARATOR_RE)
    .map((chunk) => chunk.trim())
    .filter((chunk) => chunk.length > 0);
  const tokens = chunks.flatMap((chunk) => splitToken(chunk, itemKind));
  if (itemKind === "string") return { values: tokens, invalidTokens: [] };
  const values = [];
  const invalidTokens = [];
  for (const token of tokens) {
    const value = Number(token.replace(",", "."));
    if (Number.isFinite(value)) values.push(value);
    else invalidTokens.push(token);
  }
  return { values, invalidTokens };
}

// Canonical display text for a parsed array -- decimal comma, "; " separated. Used to prefill a
// default/example/restored value into the field, for the live chips, and for the report's Dati di
// ingresso ("5; 10; 15,5 min", relazione-inputs.js appends the unit itself).
export function formatListText(values, itemKind = "number") {
  if (!Array.isArray(values)) return "";
  if (itemKind === "string") return values.join("; ");
  return values.map((value) => String(value).replace(".", ",")).join("; ");
}

// Italian message for a token that failed to parse (WORKBENCH_SPEC copy rule: say what is wrong
// and how to fix it).
export function listTokenErrorMessage(invalidTokens) {
  return `Valori non numerici: ${invalidTokens.join(", ")} — usa numeri separati da virgola, punto e virgola, spazio o a capo.`;
}

// Bounds check on an already-parsed array: minItems/maxItems (item COUNT) and, when the schema's
// `items` carried its own minimum/maximum, a per-value range check.
export function listBoundsMessage(field, values) {
  const min = field.minItems ?? 0;
  if (values.length < min) return `Servono almeno ${min} valori (inseriti ${values.length}).`;
  if (typeof field.maxItems === "number" && values.length > field.maxItems) {
    return `Massimo ${field.maxItems} valori (inseriti ${values.length}).`;
  }
  if (typeof field.itemMinimum === "number") {
    const bad = values.find((value) => value < field.itemMinimum);
    if (bad !== undefined) return `Ogni valore deve essere >= ${String(field.itemMinimum).replace(".", ",")}.`;
  }
  if (typeof field.itemMaximum === "number") {
    const bad = values.find((value) => value > field.itemMaximum);
    if (bad !== undefined) return `Ogni valore deve essere <= ${String(field.itemMaximum).replace(".", ",")}.`;
  }
  return null;
}

function renderChips(chipsEl, text, itemKind) {
  const { values, invalidTokens } = parseListText(text, itemKind);
  clear(chipsEl);
  for (const value of values) chipsEl.append(el("span", { class: "f-list-chip", text: formatListText([value], itemKind) }));
  for (const token of invalidTokens) chipsEl.append(el("span", { class: "f-list-chip f-list-chip--invalid", text: token }));
}

// `fields.js buildControl` calls this for `field.kind === "list"`; `unitId` is the SAME id the
// generic unit-suffix mechanism would have used (fields.js skips that mechanism for this kind and
// lets the widget own its own unit text instead -- a two-row text+chips control does not fit the
// single-line absolute-positioned suffix every other kind uses).
export function buildListField(field, id, describedById, unitId) {
  const input = el("input", {
    type: "text",
    id,
    name: field.name,
    "aria-describedby": describedById,
    inputmode: field.itemKind === "string" ? undefined : "decimal",
    placeholder: field.itemKind === "string" ? "valore1, valore2, …" : "5; 10; 15,5",
  });
  input.value = formatListText(field.default, field.itemKind);
  const chips = el("div", { class: "f-list-chips", "aria-hidden": "true" });
  renderChips(chips, input.value, field.itemKind);
  input.addEventListener("input", () => renderChips(chips, input.value, field.itemKind));
  const children = [input, chips];
  if (field.unit) children.push(el("span", { class: "f-list-unit", id: unitId || undefined, text: field.unit }));
  return el("div", { class: "f-list-input" }, children);
}

// `{value, error}` is not the shape here -- readValue (fields.js) wants the SAME convention the
// "number" kind already uses: the raw text back (not the array) when a token failed to parse, so
// validate.js can flag it as a real error instead of silently accepting a shorter list.
export function readListValue(form, field) {
  const input = form.elements.namedItem(field.name);
  if (!input) return undefined;
  const raw = input.value.trim();
  if (raw === "") return null;
  const { values, invalidTokens } = parseListText(raw, field.itemKind);
  return invalidTokens.length > 0 ? raw : values;
}

// Programmatic fill (Carica esempio, Azzera dati, restored inputs / share-link params) -- mirrors
// `setValue`'s contract (fields.js) but also has to repaint the chips, which no native DOM event
// fires for a value written directly to `.value`.
export function setListValue(form, field, value) {
  const input = form.elements.namedItem(field.name);
  if (!input) return;
  input.value = formatListText(Array.isArray(value) ? value : [], field.itemKind);
  const chips = input.closest(".f-list-input")?.querySelector(".f-list-chips");
  if (chips) renderChips(chips, input.value, field.itemKind);
}
