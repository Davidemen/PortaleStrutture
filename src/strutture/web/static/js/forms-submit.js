// Run-result / run-network-error handling for the form built by forms.js: maps server/located
// errors back onto fields and table cells, and reports the busy state. Split out of forms.js
// (module-length guideline); reads/writes the shared `current` state forms.js exports (mutated
// in place there, never reassigned, so this live import stays valid across tool switches).
import { current } from "./forms.js";
import { parseServerErrors, mapLocatedErrors } from "./validate.js";
import { setCellError } from "./table-input.js";

// DESIGN_SPEC §4b: located table-cell errors also get a summary entry, e.g.
// "Stratigrafia, riga 3, Modulo: ..." (using `table.key` for the row label when present).
function tableErrorSummary(byTable, fields) {
  return Object.entries(byTable || {}).flatMap(([name, cellErrors]) => {
    const field = fields.find((f) => f.name === name);
    const label = field ? field.label : name;
    return cellErrors.map(({ row, column, message }) => {
      const col = field && (field.columns || []).find((c) => c.name === column);
      return `${label}, riga ${row + 1}, ${col ? col.label : column}: ${message}`;
    });
  });
}

document.addEventListener("strutture:run-start", (event) => {
  if (current.api && event.detail.name === current.tool) current.api.setBusy(true);
});

document.addEventListener("strutture:run-result", (event) => {
  if (!current.api || event.detail.name !== current.tool) return;
  current.api.setBusy(false);
  const { report } = event.detail;
  // `report.ok`, never the HTTP status, decides success: the backend returns 200 with
  // `ok: false` for validation/domain errors (`routes/tools.py` -- "still a successful HTTP
  // exchange"); only a transport-level failure (400/500, no report body) has no `report.ok`.
  if (report && report.ok) {
    current.api.clearErrors();
    return;
  }
  const fieldNames = current.fields.map((f) => f.name);
  const details = (report && report.error_details) || [];
  const mapped = details.length > 0 ? mapLocatedErrors(details, fieldNames) : parseServerErrors((report && report.errors) || [], fieldNames);
  const tableSummary = tableErrorSummary(mapped.byTable, current.fields);
  current.api.setFieldErrors(mapped.byField, [...mapped.general, ...tableSummary]);
  Object.entries(mapped.byTable || {}).forEach(([name, cellErrors]) => {
    const container = document.querySelector(`#form-root [data-field="${name}"].f-table`);
    if (container) cellErrors.forEach(({ row, column, message }) => setCellError(container, row, column, message));
  });
});

document.addEventListener("strutture:run-network-error", (event) => {
  if (event.detail.name !== current.tool) return;
  if (current.api) current.api.setBusy(false);
  const runError = document.getElementById("run-error");
  if (runError) {
    runError.textContent = event.detail.message;
    runError.hidden = false;
  }
});
