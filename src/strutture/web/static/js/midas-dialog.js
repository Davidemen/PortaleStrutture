// Orchestrates the MIDAS import dialog (MIDAS.md §5): a native <dialog>, focus-trapped by
// `showModal()`, walking Connessione -> Combinazioni -> Appoggi -> Importa. Registered in
// js/table-sources.js under "midas-reactions" and loaded only when the table's own "Importa da
// MIDAS" button is clicked -- this module is never imported eagerly. State building/reading
// lives here; the 4 step bodies are stateless-ish DOM builders in midas-dialog-steps.js.
import { el, clear } from "./dom.js";
import { buildStepper, setAlert, parseNodeList, connectionStep, combinationsStep, supportsStep, importStep } from "./midas-dialog-steps.js";
import { fetchMidasStatus, verifyMidasConnection, fetchMidasCombinations, fetchMidasSupports, fetchMidasReactions } from "./midas-api.js";
import { getMidasKey } from "./midas-key.js";

// Famiglia = Literal[...] (docs/architecture-batch2.md §1.2 `load_table`); used as a fallback
// when the table's own `famiglia` column has no `enumValues` (e.g. a table without that column).
const FALLBACK_FAMIGLIE = ["SLU_STR", "SLU_EQU", "SLV_STR", "SLV_EQU", "SLE_RARA", "SLE_FREQ", "SLE_QP"];
const EUROPE_RELAY_PLACEHOLDER = "https://moa-engineers-gb.midasit.com:443/gen";

export async function openImport({ columns, currentRows, setRows, message, trigger }) {
  const previouslyFocused = document.activeElement;
  const famigliaColumn = (columns || []).find((c) => c.name === "famiglia");

  const state = {
    step: 1,
    product: "gen",
    baseUrl: "",
    placeholderUrl: EUROPE_RELAY_PLACEHOLDER,
    serverKey: false,
    keyValue: getMidasKey(),
    verifyBusy: false,
    verified: null,
    combosBusy: false,
    combinations: [],
    selected: {},
    onlyActive: true,
    search: "",
    famiglieOptions: (famigliaColumn && famigliaColumn.enumValues) || FALLBACK_FAMIGLIE,
    supportsMode: "tutti",
    supportsCount: null,
    gruppo: "",
    nodiText: "",
    importMode: "sostituisci",
    importBusy: false,
    warnings: [],
    done: false,
  };

  const status = await fetchMidasStatus();
  if (status.ok) {
    state.serverKey = Boolean(status.server_key);
    state.baseUrl = status.base_url || "";
    if (status.product) state.product = status.product;
  }

  const titleId = "midas-dialog-title";
  const alertBox = el("div", { class: "midas-alert", role: "alert" });
  const stepperHost = el("div");
  const bodyHost = el("div", { class: "midas-body" });
  const actionsHost = el("div", { class: "midas-actions" });
  const dialogEl = el("dialog", { class: "midas-dialog", "aria-labelledby": titleId }, [
    el("h2", { id: titleId, text: "Importa da MIDAS" }),
    stepperHost,
    alertBox,
    bodyHost,
    actionsHost,
  ]);
  document.body.append(dialogEl);

  dialogEl.addEventListener("close", () => {
    dialogEl.remove();
    const back = previouslyFocused && typeof previouslyFocused.focus === "function" ? previouslyFocused : trigger;
    if (back) back.focus();
  });

  function buildNav() {
    clear(actionsHost);
    if (state.done) {
      actionsHost.append(el("button", { type: "button", class: "midas-btn-primary", text: "Chiudi", onclick: () => dialogEl.close() }));
      return;
    }
    actionsHost.append(
      el("button", { type: "button", class: "midas-btn", text: "Annulla", onclick: () => dialogEl.close() }),
      el("button", { type: "button", class: "midas-btn", text: "Indietro", hidden: state.step === 1, onclick: goBack }),
      el("button", {
        type: "button",
        class: "midas-btn-primary",
        text: "Avanti",
        hidden: state.step === 4,
        disabled: state.step === 1 && !state.verified,
        onclick: goNext,
      }),
    );
  }

  function renderStep() {
    setAlert(alertBox, null);
    clear(stepperHost);
    stepperHost.append(buildStepper(state.step));
    clear(bodyHost);
    if (state.step === 1) bodyHost.append(connectionStep(state, { verify }));
    if (state.step === 2) bodyHost.append(combinationsStep(state));
    if (state.step === 3) bodyHost.append(supportsStep(state));
    if (state.step === 4) bodyHost.append(importStep(state, { runImport }));
    buildNav();
  }

  function goBack() {
    state.step = Math.max(1, state.step - 1);
    renderStep();
  }

  async function goNext() {
    if (state.step === 1) {
      state.step = 2;
      state.combosBusy = true;
      renderStep();
      await loadCombinations();
    } else if (state.step === 2) {
      if (!Object.values(state.selected).some((s) => s.checked)) return setAlert(alertBox, "Seleziona almeno una combinazione.");
      state.step = 3;
      renderStep();
      await loadSupportsCount();
    } else if (state.step === 3) {
      if (state.supportsMode === "nodi" && parseNodeList(state.nodiText).error) return setAlert(alertBox, parseNodeList(state.nodiText).error);
      if (state.supportsMode === "gruppo" && !state.gruppo.trim()) return setAlert(alertBox, "Indica il nome del gruppo struttura.");
      state.step = 4;
      renderStep();
    }
  }

  async function verify() {
    state.verifyBusy = true;
    renderStep();
    const result = await verifyMidasConnection({ baseUrl: state.baseUrl, product: state.product, key: getMidasKey() });
    state.verifyBusy = false;
    state.verified = result.ok ? result : null;
    if (result.ok && result.base_url) state.baseUrl = result.base_url;
    renderStep();
    if (!result.ok) setAlert(alertBox, result.errors);
  }

  async function loadCombinations() {
    const result = await fetchMidasCombinations({ baseUrl: state.baseUrl, key: getMidasKey() });
    state.combosBusy = false;
    if (!result.ok) {
      renderStep();
      return setAlert(alertBox, result.errors);
    }
    state.combinations = result.combinations || [];
    state.selected = Object.fromEntries(state.combinations.map((c) => [c.table_name, { checked: false, famiglia: c.famiglia_suggerita || null }]));
    renderStep();
  }

  async function loadSupportsCount() {
    const result = await fetchMidasSupports({ baseUrl: state.baseUrl, key: getMidasKey() });
    if (!result.ok) return setAlert(alertBox, result.errors);
    state.supportsCount = (result.supports || []).length;
    renderStep();
  }

  async function runImport() {
    state.importBusy = true;
    renderStep();
    const combinazioni = Object.entries(state.selected)
      .filter(([, s]) => s.checked)
      .map(([table_name, s]) => ({ table_name, famiglia: s.famiglia }));
    const request = { baseUrl: state.baseUrl, combinazioni, key: getMidasKey() };
    if (state.supportsMode === "gruppo") request.gruppo = state.gruppo.trim();
    else if (state.supportsMode === "nodi") request.nodi = parseNodeList(state.nodiText).nodes;

    const result = await fetchMidasReactions(request);
    state.importBusy = false;
    if (!result.ok) {
      renderStep();
      return setAlert(alertBox, result.errors);
    }

    const rows = result.righe || [];
    setRows(state.importMode === "aggiungi" ? [...currentRows(), ...rows] : rows);
    const n = result.n_righe != null ? result.n_righe : rows.length;
    const announcement = `${n} righe importate da MIDAS.`;

    if (result.avvisi && result.avvisi.length > 0) {
      state.warnings = result.avvisi;
      state.done = true;
      renderStep();
      dialogEl.addEventListener("close", () => message(announcement), { once: true });
      return;
    }
    message(announcement);
    dialogEl.close();
  }

  renderStep();
  dialogEl.showModal();
  const firstField = dialogEl.querySelector("input, select, button");
  if (firstField) firstField.focus();
}
