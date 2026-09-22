// "Dimensiona" dialog (WORKBENCH_SPEC §23.5): a non-modal side panel offering to search for the
// smallest/largest value of one numeric Dati field for which every check passes at the chosen
// utilisation target. Orchestration only -- η/reliability rendering lives in dimensiona-esito.js,
// the pure Da/A + Campo helpers in dimensiona-modello.js, the fetch in dimensiona-api.js.
import { el, clear } from "./dom.js";
import { trapFocus } from "./nav-state.js";
import { describeFields } from "./schema.js";
import { fieldInputId } from "./fields.js";
import { parseDecimal, formatForInput } from "./number-input.js";
import { campiNumerici, prefillRange, origineTesto, groupFields } from "./dimensiona-modello.js";
import { buildEsito } from "./dimensiona-esito.js";
import { postDimensiona } from "./dimensiona-api.js";
import { passiStrumento } from "./impostazioni-api.js";
import { lastFocusedNumericField } from "./dimensiona-focus.js";

const session = { name: null, fields: [], lastValues: null, lastReport: null };
// §23.5: only these two outcomes offer "Applica" -- every other outcome shows the best sample
// instead (buildEsito's own `evidenziaMigliore`).
const APPLICA_ESITI = new Set(["trovato", "estremo_sufficiente"]);

document.addEventListener("strutture:tool-schema", (event) => {
  const { name, input } = event.detail || {};
  session.name = name;
  session.fields = describeFields(input || {});
  session.lastValues = null;
  session.lastReport = null;
});
document.addEventListener("strutture:run-request", (event) => {
  const { name, values } = event.detail || {};
  if (session.name === name) session.lastValues = values;
});
document.addEventListener("strutture:run-result", (event) => {
  const { name, report } = event.detail || {};
  if (session.name === name) session.lastReport = report;
});

function wireButton(button) {
  button.onclick = () => openDimensiona(lastFocusedNumericField());
}

document.addEventListener("strutture:results-rendered", (event) => {
  const button = document.querySelector(".dm-toggle");
  if (button) wireButton(button);
});
document.addEventListener("strutture:shortcut-dimensiona", () => {
  const button = document.querySelector(".dm-toggle");
  if (!button || button.disabled) return;
  openDimensiona(lastFocusedNumericField());
});

function applyValue(name, value) {
  const input = document.getElementById(fieldInputId(name));
  if (!input) return;
  input.value = formatForInput(value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
  const wrapper = document.querySelector(`.f-field[data-field="${name}"]`);
  if (wrapper) {
    wrapper.classList.add("f-field--flash");
    setTimeout(() => wrapper.classList.remove("f-field--flash"), 1600);
  }
}

function buildCampoSelect(fields, selected) {
  const select = el("select", { id: "dm-campo", required: true });
  const groups = groupFields(fields);
  for (const [groupName, groupFieldsList] of groups) {
    const optgroup = el("optgroup", { label: groupName });
    for (const field of groupFieldsList) {
      optgroup.append(el("option", { value: field.name, selected: field.name === selected, text: `${field.symbol ? field.symbol + " " : ""}${field.label}` }));
    }
    select.append(optgroup);
  }
  return select;
}

export function openDimensiona(preselected) {
  if (!session.name) return;
  const trigger = document.activeElement;
  const numericFields = campiNumerici(session.fields);
  if (numericFields.length === 0) return;
  const initialField = numericFields.find((f) => f.name === preselected) || numericFields[0];

  const titleId = "dm-title";
  const liveRegion = el("div", { class: "sr-only", role: "status", "aria-live": "polite" });
  const campoSelect = buildCampoSelect(numericFields, initialField.name);
  const daInput = el("input", { type: "text", id: "dm-da", inputmode: "decimal", required: true });
  const aInput = el("input", { type: "text", id: "dm-a", inputmode: "decimal", required: true });
  const passoInput = el("input", { type: "text", id: "dm-passo", inputmode: "decimal", required: true });
  const passoNote = el("p", { class: "dm-note" });
  const obiettivoInput = el("input", { type: "text", id: "dm-obiettivo", inputmode: "decimal", value: "1" });
  const minimoLine = el("p", { class: "dm-note", text: "Obiettivo anche sulle verifiche di minimo: —" });
  const versoSelect = el("select", { id: "dm-verso" }, [
    el("option", { value: "auto", text: "Automatico" }),
    el("option", { value: "minimo", text: "Valore minimo" }),
    el("option", { value: "massimo", text: "Valore massimo" }),
  ]);
  const reasonEl = el("p", { id: "dm-cerca-reason", class: "dm-note", text: "Indicare il passo di arrotondamento." });
  const cercaBtn = el("button", { type: "button", class: "dm-btn-primary", text: "Cerca", "aria-describedby": "dm-cerca-reason" });
  const annullaBtn = el("button", { type: "button", class: "dm-btn", text: "Annulla" });
  const chiudiBtn = el("button", { type: "button", class: "dm-btn", text: "Chiudi" });
  const resultHost = el("div", { class: "dm-result" });
  const busyEl = el("p", { class: "dm-busy", hidden: true, text: "Ricerca in corso…" });

  const form = el("form", { class: "dm-form" }, [
    el("div", { class: "dm-row" }, [el("label", { for: "dm-campo", text: "Campo" }), campoSelect]),
    el("div", { class: "dm-row-pair" }, [
      el("div", {}, [el("label", { for: "dm-da", text: "Da" }), daInput]),
      el("div", {}, [el("label", { for: "dm-a", text: "A" }), aInput]),
    ]),
    el("div", { class: "dm-row" }, [el("label", { for: "dm-passo", text: "Passo" }), passoInput, passoNote]),
    el("div", { class: "dm-row" }, [el("label", { for: "dm-obiettivo", text: "Obiettivo di sfruttamento" }), obiettivoInput]),
    minimoLine,
    el("div", { class: "dm-row" }, [el("label", { for: "dm-verso", text: "Verso" }), versoSelect]),
    reasonEl,
    el("div", { class: "dm-actions" }, [cercaBtn, annullaBtn]),
    busyEl,
    resultHost,
  ]);

  const panel = el("div", { class: "dm-panel", role: "dialog", "aria-labelledby": titleId }, [
    el("h2", { id: titleId, text: "Dimensiona" }),
    form,
    chiudiBtn,
    liveRegion,
  ]);

  document.body.append(panel);
  let release = null;
  let controller = null;

  function close() {
    if (controller) controller.abort();
    document.body.classList.remove("dm-open");
    panel.remove();
    if (release) release();
    if (trigger && typeof trigger.focus === "function") trigger.focus();
  }

  chiudiBtn.onclick = close;
  annullaBtn.onclick = () => {
    if (controller) controller.abort();
  };

  function updateReason() {
    const passoOk = parseDecimal(passoInput.value) !== null && parseDecimal(passoInput.value) > 0;
    const daOk = daInput.value.trim() !== "" && aInput.value.trim() !== "";
    const ok = passoOk && daOk;
    // §23.5: "disabled with aria-disabled + aria-describedby ... still reachable by Tab" -- the
    // NATIVE `disabled` attribute would remove it from the tab order entirely, so only the ARIA
    // state is toggled; `runSearch`/the Ctrl+Enter handler both re-check `aria-disabled` instead.
    cercaBtn.setAttribute("aria-disabled", String(!ok));
    reasonEl.hidden = ok;
  }
  [daInput, aInput, passoInput].forEach((input) => input.addEventListener("input", updateReason));
  // §23.1: "changing Campo re-resolves [Passo] unless the user already typed one" -- only a real
  // keystroke sets this (programmatic writes below never dispatch `input`), so a settings fetch
  // that resolves late never clobbers a value the engineer already typed.
  let userEditedPasso = false;
  passoInput.addEventListener("input", () => {
    userEditedPasso = true;
  });

  function applyPrefill(field) {
    const current = session.lastValues ? session.lastValues[field.name] : undefined;
    const { da, a } = prefillRange(field, current);
    daInput.value = da !== null ? formatForInput(da) : "";
    aInput.value = a !== null ? formatForInput(a) : "";
  }

  function applyPassiSettings(field) {
    passiStrumento(session.name)
      .then((body) => {
        obiettivoInput.value = formatForInput(body.obiettivo_sfruttamento ?? 1);
        minimoLine.textContent = `Obiettivo anche sulle verifiche di minimo: ${body.obiettivo_su_verifiche_minimo ? "sì" : "no"} (Impostazioni)`;
        const info = body.passi ? body.passi[field.name] : null;
        if (!userEditedPasso) {
          if (info && info.passo != null) {
            passoInput.value = formatForInput(info.passo);
          } else {
            passoInput.value = "";
          }
        }
        passoNote.textContent = info && info.passo != null ? origineTesto(info.origine) : "";
        updateReason();
      })
      .catch(() => {
        passoNote.textContent = "Impostazioni non disponibili: valori di fabbrica.";
        obiettivoInput.value = "1";
        updateReason();
      });
  }

  function onCampoChange() {
    const field = numericFields.find((f) => f.name === campoSelect.value);
    if (!field) return;
    applyPrefill(field);
    applyPassiSettings(field);
  }
  campoSelect.addEventListener("change", onCampoChange);

  applyPrefill(initialField);
  applyPassiSettings(initialField);

  function runSearch() {
    const field = numericFields.find((f) => f.name === campoSelect.value);
    const body = {
      inputs: session.lastValues || {},
      campo: field.name,
      da: parseDecimal(daInput.value),
      a: parseDecimal(aInput.value),
      passo: parseDecimal(passoInput.value),
      obiettivo: parseDecimal(obiettivoInput.value) ?? 1,
      verso: versoSelect.value,
    };
    // A second Cerca while one is already running (double-click, repeated Ctrl+Enter) must cancel
    // the FIRST request, never run both -- two in flight could resolve out of order and leave a
    // stale result on screen after the newer one, or double up on the visible result blocks below.
    if (controller) controller.abort();
    controller = new AbortController();
    const myController = controller; // settle handlers below only act if still THIS request
    cercaBtn.setAttribute("aria-disabled", "true");
    busyEl.hidden = false;
    liveRegion.textContent = "Ricerca in corso…";
    clear(resultHost);
    postDimensiona(session.name, body, myController.signal)
      .then((result) => {
        if (controller !== myController) return; // superseded by a later Cerca before this settled
        controller = null;
        updateReason(); // restores aria-disabled to whatever Da/A/Passo actually allow
        busyEl.hidden = true;
        if (!result.ok) {
          const message = (result.body && result.body.errors && result.body.errors[0]) || "Impossibile completare la ricerca.";
          resultHost.append(el("p", { class: "dm-errore", role: "alert", text: message }));
          liveRegion.textContent = message;
          return;
        }
        const esito = result.body;
        resultHost.append(buildEsito(field, esito, { evidenziaMigliore: !APPLICA_ESITI.has(esito.esito) }));
        // §23.5: Applica only for "trovato"/"estremo_sufficiente" -- "nessun_valore"/"interrotta"/
        // "limite_validita" show the best sample instead (buildEsito, above), never a value to
        // apply outright (a "limite_validita" `valore` IS the method's own validity boundary, not
        // a value the calculation actually endorses).
        if (APPLICA_ESITI.has(esito.esito) && esito.valore !== null && esito.valore !== undefined) {
          const applicaBtn = el("button", { type: "button", class: "dm-btn-primary", text: "Applica" });
          applicaBtn.onclick = () => applyValue(field.name, esito.valore);
          resultHost.append(applicaBtn);
        }
        const sensBtn = el("button", { type: "button", class: "dm-btn", text: "Studia la sensibilità" });
        sensBtn.onclick = () => {
          close();
          import("./sensibilita.js").then(({ openSensibilita }) => {
            openSensibilita(field.name, { da: parseDecimal(daInput.value), a: parseDecimal(aInput.value) });
          });
        };
        resultHost.append(sensBtn);
        liveRegion.textContent = `${field.symbol || field.label} = ${esito.valore ?? "—"}, ${esito.affidabile ? "affidabile" : "da controllare"}`;
      })
      .catch((error) => {
        if (controller !== myController) return; // this one was already superseded/aborted-and-replaced
        controller = null;
        updateReason();
        busyEl.hidden = true;
        if (error && error.name === "AbortError") {
          liveRegion.textContent = "Ricerca annullata.";
          return;
        }
        resultHost.append(el("p", { class: "dm-errore", role: "alert", text: "Impossibile contattare il server." }));
      });
  }

  cercaBtn.onclick = () => {
    if (cercaBtn.getAttribute("aria-disabled") !== "true") runSearch();
  };
  // §23.5: "Cerca (Enter inside the dialog)" -- plain Enter anywhere in the form, not just
  // Ctrl+Enter (kept too, for muscle memory with the rest of the app's own shortcuts). Excludes a
  // focused <button>/<select>: Enter already activates/does nothing useful on those natively, so
  // triggering Cerca there too would fire it twice for a button (once native, once here) or
  // hijack a <select>'s own Enter-to-close behaviour.
  form.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const tag = event.target.tagName;
    if (tag === "BUTTON" || tag === "SELECT") return;
    event.preventDefault();
    event.stopPropagation();
    if (cercaBtn.getAttribute("aria-disabled") !== "true") runSearch();
  });

  updateReason();
  document.body.classList.add("dm-open");
  // §23.5: Esc DURING a search only cancels that search (the dialog stays open, exactly like
  // Annulla); a plain close is still Esc's job the rest of the time.
  release = trapFocus(panel, { onEscape: () => (controller ? controller.abort() : close()) });
  campoSelect.focus();
}
