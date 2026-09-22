// Remembers the last-focused numeric Dati field (WORKBENCH_SPEC §23.5/§24.2): `g d`/`g s`
// preselect the dialog on it instead of always opening on the first numeric field. A single
// `focusin` listener, shared by js/dimensiona.js and js/sensibilita.js so neither has to attach
// its own.
let lastNumericField = null;

document.addEventListener("focusin", (event) => {
  const target = event.target;
  if (!target || typeof target.closest !== "function") return;
  const wrapper = target.closest(".f-field[data-field]");
  if (!wrapper || !wrapper.contains(target)) return;
  if (!target.classList || !target.classList.contains("f-number")) return;
  lastNumericField = wrapper.dataset.field;
});

document.addEventListener("strutture:tool-schema", () => {
  lastNumericField = null;
});

export function lastFocusedNumericField() {
  return lastNumericField;
}
