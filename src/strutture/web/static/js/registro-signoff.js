// The sign-off form (WORKBENCH_SPEC §13.1): three state radios, sigla (required unless "Da
// confermare", 1-12 characters -- same rule the server enforces, `routes/divergences.py`
// `_SIGLA_REQUIRED_IT`), a free-text nota and "Salva decisione". Reused for a single row's own
// form AND the bulk "Decidi per le N selezionate..." form -- both just supply a different
// `idPrefix` (unique radio group names) and `onSubmit` (single signoff vs signoff-multiplo).
// Never updates anything itself: `onSubmit` returns a Promise, and the caller's own `.then` is
// what applies the confirmed change -- "the row updates only after the server confirms".
import { el } from "./dom.js";

const STATI = [
  ["da_confermare", "Da confermare"],
  ["approvato", "Approvata"],
  ["respinto", "Respinta"],
];

const SIGLA_REQUIRED_MESSAGE = "La sigla è obbligatoria per approvare o respingere (1-12 caratteri).";

export function buildSignoffForm({ idPrefix, initial = {}, submitLabel = "Salva decisione", onSubmit }) {
  const errorEl = el("p", { class: "reg-form-error", role: "alert", hidden: true });
  const statusEl = el("p", { class: "reg-form-status", role: "status" });
  const statoName = `${idPrefix}-stato`;
  const radios = STATI.map(([value, label]) => {
    const inputId = `${statoName}-${value}`;
    const checked = (initial.stato || "da_confermare") === value;
    const input = el("input", { type: "radio", name: statoName, id: inputId, value, checked: checked || undefined });
    const labelEl = el("label", { class: "reg-radio", for: inputId }, [input, document.createTextNode(` ${label}`)]);
    return { input, labelEl };
  });

  const siglaId = `${idPrefix}-sigla`;
  const siglaInput = el("input", { type: "text", id: siglaId, maxlength: "12", value: initial.sigla || "" });
  const notaId = `${idPrefix}-nota`;
  const notaInput = el("textarea", { id: notaId, maxlength: "2000", rows: "2" });
  notaInput.value = initial.nota || "";
  const submitBtn = el("button", { type: "submit", class: "reg-form-save", text: submitLabel });

  const form = el("form", { class: "reg-form", novalidate: true }, [
    el("fieldset", { class: "reg-form-stato" }, [el("legend", { text: "Stato" }), ...radios.map((r) => r.labelEl)]),
    el("div", { class: "reg-form-field" }, [el("label", { for: siglaId, text: "Sigla" }), siglaInput]),
    el("div", { class: "reg-form-field" }, [el("label", { for: notaId, text: "Nota" }), notaInput]),
    errorEl,
    submitBtn,
    statusEl,
  ]);

  function currentStato() {
    const checked = radios.find((r) => r.input.checked);
    return checked ? checked.input.value : "da_confermare";
  }

  function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = false;
  }

  function clearError() {
    errorEl.hidden = true;
    errorEl.textContent = "";
  }

  function setBusy(busy) {
    submitBtn.disabled = busy;
    submitBtn.textContent = busy ? "Salvataggio…" : submitLabel;
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearError();
    statusEl.textContent = "";
    const stato = currentStato();
    const sigla = siglaInput.value.trim();
    if (stato !== "da_confermare" && (sigla.length < 1 || sigla.length > 12)) {
      showError(SIGLA_REQUIRED_MESSAGE);
      siglaInput.focus();
      return;
    }
    setBusy(true);
    onSubmit({ stato, sigla, nota: notaInput.value })
      .then(() => {
        setBusy(false);
        statusEl.textContent = "Decisione salvata.";
      })
      .catch((error) => {
        setBusy(false);
        showError((error && error.message) || "Impossibile salvare la decisione.");
      });
  });

  return { form, siglaInput };
}
