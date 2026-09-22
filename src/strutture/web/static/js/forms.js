// Builds the input form (accordion sections, conditions, unit selector, sticky action bar) and
// self-wires to the shared `strutture:*` events: listens for `tool-schema`/`run-start`/
// `run-result`, dispatches `strutture:inputs-changed` on every edit (live.js debounces the actual
// run from there). Section/summary/unit-selector builders live in forms-sections.js, the accordion
// DOM in form-sections-summary.js, the run-result / run-network-error handling in forms-submit.js
// (imported below for its side effects -- it reads/writes the shared `current` state exported here).
import { el, clear } from "./dom.js";
import { describeFields } from "./schema.js";
import { buildField, setValue, setFieldError } from "./fields.js";
import { validateValues } from "./validate.js";
import { save, load, fromParams, clearStored } from "./form-state.js";
import { groupFields, rawValues, visibleValues, applyConditions, wireUnitSelector, renderSummary, copyShareLink } from "./forms-sections.js";
import { buildSections } from "./form-sections-summary.js";
import { requestRun, isLiveEnabled } from "./live.js";
import { mountElementoSalva, activeElementoOrigine } from "./elemento-salva.js";
import { mountVariantiBar } from "./varianti-bar.js";
import { mountProvenienza } from "./provenienza.js";
import { mountExcelRitirato } from "./excel-ritirato.js";
import { mountAnnullaUi } from "./annulla-ui.js";
import "./forms-submit.js";

const FORM_ID = "tool-form";

function printRelazione() {
  const trigger = document.querySelector(".r-print-trigger");
  if (trigger) trigger.click();
  else window.print();
}

const MENU_OPENS_RIGHT = "f-menu--destra";

function buildMenu(form, fields, tool) {
  const menu = el("details", { class: "f-menu" });
  const copyLinkButton = el("button", {
    type: "button",
    class: "f-menu-item",
    text: "Copia link",
    onclick: () => copyShareLink(form, fields, tool, copyLinkButton),
  });
  const resetButton = el("button", {
    type: "button",
    class: "f-menu-item",
    text: "Azzera dati",
    onclick: () => {
      fields.forEach((field) => setValue(form, field, field.default));
      clearStored(tool);
      // WORKBENCH_SPEC §21.1: names this one undo step outright ("Azzera dati" touches every
      // field at once, so js/annulla-ui.js's own diff would otherwise fall back to a generic
      // label) -- consumed by its `change` listener, never read by anything else.
      form.dataset.annullaLabel = "Azzera dati";
      form.dispatchEvent(new Event("change", { bubbles: true }));
      menu.open = false;
    },
  });
  const printButton = el("button", {
    type: "button",
    class: "f-menu-item",
    text: "Stampa relazione",
    onclick: () => {
      printRelazione();
      menu.open = false;
    },
  });
  menu.append(el("summary", { class: "f-menu-btn", "aria-label": "Altre azioni" }, [document.createTextNode("⋯")]));
  const list = el("div", { class: "f-menu-list" }, [copyLinkButton, resetButton, printButton]);
  menu.append(list);
  // The list is right-aligned to the "⋯" button. When the action bar wraps (saved element +
  // narrow Dati column) the button sits at the LEFT edge and a right-aligned list would open
  // under the sidebar: measure on open and flip it to open rightwards instead.
  menu.addEventListener("toggle", () => {
    if (!menu.open) return;
    const bar = menu.parentElement.getBoundingClientRect();
    const button = menu.getBoundingClientRect();
    menu.classList.toggle(MENU_OPENS_RIGHT, button.right - list.offsetWidth < bar.left);
  });
  return menu;
}

// `renderForm(root, {fields, example, initialValues}) -> FormApi`, per DESIGN_SPEC §5, extended
// per WORKBENCH_SPEC §2/§3. `tool` is needed for persistence/share-link/live-session keying.
export function renderForm(root, { fields = [], example = null, initialValues = {}, tool = "", params = {}, title = "", input = {} } = {}) {
  clear(root);
  const actions = document.getElementById("form-actions");
  if (actions) clear(actions);

  const form = el("form", { id: FORM_ID, class: "f-form", novalidate: true, "aria-busy": "false" });
  const { sections, advanced } = groupFields(fields);

  const sectionsApi = buildSections(sections, tool);
  form.append(
    el("div", { class: "f-section-tools" }, [
      el("button", { type: "button", class: "f-section-tools-btn", text: "Espandi tutto", onclick: () => sectionsApi.expandAll() }),
      el("button", { type: "button", class: "f-section-tools-btn", text: "Comprimi tutto", onclick: () => sectionsApi.collapseAll() }),
    ]),
    ...sectionsApi.elements,
  );
  if (advanced.length > 0) {
    const details = el("details", { class: "f-section f-advanced" });
    details.append(el("summary", { text: "Avanzate" }));
    advanced.forEach((field) => details.append(buildField(field)));
    form.append(details);
  }
  root.append(form);

  fields.forEach((field) => setValue(form, field, initialValues[field.name] ?? field.default));
  applyConditions(form, fields);
  wireUnitSelector(form, fields);

  let currentErrors = {};
  const calcolaButton = el("button", { type: "submit", form: FORM_ID, class: "f-run-button", text: "Calcola" });
  // Finding F: one row, always -- when live calculation is on (Calcola hidden) this quiet status
  // text fills the space it would otherwise leave empty, instead of nothing at all.
  const liveStatus = el("span", { class: "f-live-status" });
  const exampleButton = el("button", {
    type: "button",
    class: "f-example-button",
    text: "Carica esempio",
    hidden: example == null,
    onclick: () => {
      fields.forEach((field) => setValue(form, field, example ? example[field.name] : undefined));
      const { values, errors } = validateAndRender();
      // `setValue()` writes the DOM control's `.value` directly, which fires no native
      // "input"/"change" event, so `handleChange()` (and its own `save()` call) never runs for
      // this path -- persist here too, or "Carica esempio" then reload would silently forget the
      // example (DESIGN_SPEC P1 / WORKBENCH_SPEC §9 "reload restores the last inputs").
      if (Object.keys(errors).length === 0) {
        save(tool, values, fields);
        requestRun(tool, values, "example");
        // WORKBENCH_SPEC §21.1: "Carica esempio" is one undoable step. A dedicated event, not
        // `change` -- js/forms.js already ran its own full pipeline above (`validateAndRender`,
        // `save`, `requestRun`), so dispatching `change` too would run it a second time for nothing.
        document.dispatchEvent(new CustomEvent("strutture:annulla-commit", { detail: { label: "Carica esempio" } }));
      }
    },
  });
  // WORKBENCH_SPEC §14.1: "Salva in progetto" next to "Carica esempio". `getApi` is a live
  // accessor (not the `api` object itself, still a few lines from being assigned below) -- its
  // own dialog/deep-link handlers only ever call it once the engineer has interacted with the
  // page, by which time `api` is long since assigned, so the temporal-dead-zone read is safe.
  let api;
  // WORKBENCH_SPEC §21.1: "Annulla"/"Ripristina" in the Dati action bar (own line below the
  // others -- see the `actions.append(...)` comment further down). Same lazy `getApi` accessor as
  // the two widgets below.
  const annullaWidget = mountAnnullaUi({ tool, fields, getApi: () => api });
  const salvaWidget = mountElementoSalva({ toolForm: form, tool, title, fields, params, input, getApi: () => api });
  // WORKBENCH_SPEC §19.2: "Crea variante" next to "Carica esempio"; the strip itself is placed
  // above the form, below the §15/§16 notices, further down.
  const variantiApi = mountVariantiBar({ tool, fields, getApi: () => api, getOrigine: activeElementoOrigine });
  // WORKBENCH_SPEC §15/§16: both dismissible notices go directly above the form, under the tool
  // title -- `root.insertBefore(node, form)` places each one right before `form` (already `root`'s
  // only child at this point), so calling it twice, in this order, stacks them provenienza-note-
  // then-excel-note-then-form without needing a dedicated notices container in index.html.
  const provenienzaNote = mountProvenienza({ toolForm: form, tool, fields, params, input, getApi: () => api });
  const excelNote = mountExcelRitirato({ toolForm: form, tool });
  root.insertBefore(provenienzaNote, form);
  root.insertBefore(excelNote, form);
  root.insertBefore(variantiApi.stripElement, form);
  // `annullaWidget` renders on its OWN line below (`.an-widget { flex-basis: 100% }`, forms.css):
  // WORKBENCH_SPEC finding F's "the action bar stays on one row" is a permanent test
  // (`test_dati_action_bar_is_one_row`) that already leaves this row no spare width for two more
  // full-width buttons -- appended last so tab order still matches the visual order.
  if (actions) {
    actions.append(exampleButton, variantiApi.creaButton, salvaWidget, calcolaButton, liveStatus, buildMenu(form, fields, tool), annullaWidget);
  }

  function updateRunUi(values) {
    const live = isLiveEnabled(values);
    calcolaButton.hidden = live;
    liveStatus.textContent = live ? "Calcolo automatico attivo" : "";
  }

  // Shared by every change path (typing, table edits, example, submit): re-applies conditions,
  // re-validates, paints inline + summary errors, refreshes the accordion previews/badges and the
  // "Calcola" button's visibility (only shown while live is off, WORKBENCH_SPEC §3).
  function validateAndRender() {
    applyConditions(form, fields);
    const values = visibleValues(form, fields);
    const errors = validateValues(fields, values);
    currentErrors = errors;
    fields.forEach((field) => setFieldError(form, field.name, errors[field.name] || null));
    renderSummary(fields, errors, []);
    sectionsApi.refresh(values, errors);
    updateRunUi(values);
    return { values, errors };
  }

  function handleChange() {
    const { values, errors } = validateAndRender();
    const valid = Object.keys(errors).length === 0;
    // Persist on every valid edit, not only an explicit Calcola submit: live calculation
    // (WORKBENCH_SPEC §2) means most runs never fire the form's native "submit" event at all
    // (debounced typing, Ctrl+Enter from live.js's own keydown listener) -- restricting `save()`
    // to that one path would silently stop remembering inputs for anyone who never presses
    // Calcola, breaking "reload restores the last inputs" (DESIGN_SPEC P1 / WORKBENCH_SPEC §9).
    if (valid) {
      save(tool, values, fields);
      // WORKBENCH_SPEC §19.2: "Every valid form change updates the active variant's inputs".
      variantiApi.onValidChange(values);
    }
    document.dispatchEvent(
      new CustomEvent("strutture:inputs-changed", {
        detail: { name: tool, values, valid },
        bubbles: true,
      }),
    );
  }
  form.addEventListener("input", handleChange);
  form.addEventListener("change", handleChange);

  // Initial paint: summaries + button state, but no error noise on a form nobody has touched yet.
  sectionsApi.refresh(visibleValues(form, fields), {});
  updateRunUi(visibleValues(form, fields));

  api = {
    values: () => visibleValues(form, fields),
    // WORKBENCH_SPEC §21.2: every field's CURRENT value, hidden conditional ones included -- the
    // undo snapshot (`values()`/`visibleValues` fall a hidden field back to its default/minimum,
    // which would silently drop what was typed under a switch the moment it is hidden again).
    allValues: () => rawValues(form, fields),
    setValues: (values) => {
      fields.forEach((field) => setValue(form, field, values[field.name]));
      validateAndRender();
    },
    setFieldErrors: (byField, general = []) => {
      fields.forEach((field) => setFieldError(form, field.name, byField[field.name] || null));
      currentErrors = byField;
      renderSummary(fields, byField, general);
      sectionsApi.refresh(visibleValues(form, fields), byField);
    },
    clearErrors: () => {
      fields.forEach((field) => setFieldError(form, field.name, null));
      currentErrors = {};
      renderSummary(fields, {}, []);
      sectionsApi.refresh(visibleValues(form, fields), {});
    },
    setBusy: (busy) => {
      form.setAttribute("aria-busy", String(busy));
      calcolaButton.disabled = busy;
      calcolaButton.textContent = busy ? "Calcolo…" : "Calcola";
    },
    applyConditions: () => applyConditions(form, fields),
    // Finding F: the header "Calcolo automatico" switch (shell) changes whether Calcola/the
    // status text show WITHOUT the engineer touching a field -- re-paint on that event too, not
    // only on the next edit.
    refreshRunUi: () => updateRunUi(visibleValues(form, fields)),
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const { values, errors } = validateAndRender();
    if (Object.keys(errors).length > 0) {
      const firstInvalid = form.querySelector('[aria-invalid="true"]');
      if (firstInvalid) firstInvalid.focus();
      return;
    }
    save(tool, values, fields);
    requestRun(tool, values, "manual");
  });

  return api;
}

// Self-wiring: rebuilds the form on every tool selection. Mutated in place (never reassigned)
// so forms-submit.js can hold a live reference to the same object.
export const current = { tool: null, fields: [], api: null };

document.addEventListener("strutture:tool-schema", (event) => {
  const { name, input, example, params, title } = event.detail;
  const root = document.getElementById("form-root");
  if (!root) return;
  const fields = describeFields(input || {});
  const defaults = Object.fromEntries(fields.filter((f) => f.default !== undefined).map((f) => [f.name, f.default]));
  const initialValues = { ...defaults, ...(load(name) || {}), ...fromParams(params || {}, fields) };
  current.tool = name;
  current.fields = fields;
  current.api = renderForm(root, { fields, example, initialValues, tool: name, params: params || {}, title, input: input || {} });
});

document.addEventListener("strutture:live-setting", () => {
  if (current.api) current.api.refreshRunUi();
});
