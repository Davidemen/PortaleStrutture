// "Sensibilità" dialog (WORKBENCH_SPEC §24.2): studies how every check reacts to one input over a
// range. Orchestration only -- chart data prep in sensibilita-grafico.js, the accessible table in
// sensibilita-tabella.js, the fetch in dimensiona-api.js (same router as "Dimensiona").
import { el, clear } from "./dom.js";
import { trapFocus } from "./nav-state.js";
import { describeFields } from "./schema.js";
import { fieldInputId } from "./fields.js";
import { parseDecimal, formatForInput } from "./number-input.js";
import { campiNumerici, prefillRange, groupFields } from "./dimensiona-modello.js";
import { postSensibilita } from "./dimensiona-api.js";
import { passiStrumento } from "./impostazioni-api.js";
import { lastFocusedNumericField } from "./dimensiona-focus.js";
import { renderChart } from "./chart.js";
import { selectTopChecks, buildRows, buildSeries, buildGuides, buildHGuides, ETA_MAX_GRAFICO, MAX_SERIE } from "./sensibilita-grafico.js";
import { buildTabella } from "./sensibilita-tabella.js";
import { formatUnit } from "./format.js";

const session = { name: null, fields: [], lastValues: null };

document.addEventListener("strutture:tool-schema", (event) => {
  const { name, input } = event.detail || {};
  session.name = name;
  session.fields = describeFields(input || {});
  session.lastValues = null;
});
document.addEventListener("strutture:run-request", (event) => {
  const { name, values } = event.detail || {};
  if (session.name === name) session.lastValues = values;
});

document.addEventListener("strutture:results-rendered", () => {
  const button = document.querySelector(".sv-toggle");
  if (button) button.onclick = () => openSensibilita(lastFocusedNumericField());
});
document.addEventListener("strutture:shortcut-sensibilita", () => {
  const button = document.querySelector(".sv-toggle");
  if (!button || button.disabled) return;
  openSensibilita(lastFocusedNumericField());
});

function applyValue(name, value) {
  const input = document.getElementById(fieldInputId(name));
  if (!input) return;
  input.value = formatForInput(value);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
}

function buildCampoSelect(fields, selected) {
  const select = el("select", { id: "sv-campo", required: true });
  for (const [groupName, groupFieldsList] of groupFields(fields)) {
    const optgroup = el("optgroup", { label: groupName });
    for (const field of groupFieldsList) {
      optgroup.append(el("option", { value: field.name, selected: field.name === selected, text: `${field.symbol ? field.symbol + " " : ""}${field.label}` }));
    }
    select.append(optgroup);
  }
  return select;
}

// `range` = {da, a} pre-filled by dimensiona.js's "Studia la sensibilità" button.
export function openSensibilita(preselected, range) {
  if (!session.name) return;
  const trigger = document.activeElement;
  const numericFields = campiNumerici(session.fields);
  if (numericFields.length === 0) return;
  const initialField = numericFields.find((f) => f.name === preselected) || numericFields[0];

  const titleId = "sv-title";
  const liveRegion = el("div", { class: "sr-only", role: "status", "aria-live": "polite" });
  const campoSelect = buildCampoSelect(numericFields, initialField.name);
  const daInput = el("input", { type: "text", id: "sv-da", inputmode: "decimal", required: true });
  const aInput = el("input", { type: "text", id: "sv-a", inputmode: "decimal", required: true });
  const puntiInput = el("input", { type: "text", id: "sv-punti", inputmode: "numeric", value: "21" });
  const obiettivoInput = el("input", { type: "text", id: "sv-obiettivo", inputmode: "decimal", value: "1" });
  const calcolaBtn = el("button", { type: "button", class: "sv-btn-primary", text: "Calcola" });
  const chiudiBtn = el("button", { type: "button", class: "sv-btn", text: "Chiudi" });
  const busyEl = el("p", { class: "sv-busy", hidden: true, text: "Ricerca in corso…" });
  const resultHost = el("div", { class: "sv-result" });

  const form = el("form", { class: "sv-form" }, [
    el("div", { class: "sv-row" }, [el("label", { for: "sv-campo", text: "Campo" }), campoSelect]),
    el("div", { class: "sv-row-pair" }, [
      el("div", {}, [el("label", { for: "sv-da", text: "Da" }), daInput]),
      el("div", {}, [el("label", { for: "sv-a", text: "A" }), aInput]),
    ]),
    el("div", { class: "sv-row" }, [el("label", { for: "sv-punti", text: "Punti" }), puntiInput]),
    el("div", { class: "sv-row" }, [el("label", { for: "sv-obiettivo", text: "Obiettivo" }), obiettivoInput]),
    el("div", { class: "sv-actions" }, [calcolaBtn]),
    busyEl,
    resultHost,
  ]);

  const panel = el("div", { class: "sv-panel", role: "dialog", "aria-labelledby": titleId }, [
    el("h2", { id: titleId, text: "Sensibilità" }),
    form,
    chiudiBtn,
    liveRegion,
  ]);
  document.body.append(panel);

  function close() {
    document.body.classList.remove("sv-open");
    panel.remove();
    if (release) release();
    if (trigger && typeof trigger.focus === "function") trigger.focus();
  }
  chiudiBtn.onclick = close;

  let release = null;
  let lastResponse = null;
  let selectedKeys = null; // null = default (top-5); Set once the user touches a checkbox

  function applyPrefill(field) {
    if (range && Number.isFinite(range.da) && Number.isFinite(range.a)) {
      daInput.value = formatForInput(range.da);
      aInput.value = formatForInput(range.a);
      return;
    }
    const current = session.lastValues ? session.lastValues[field.name] : undefined;
    const { da, a } = prefillRange(field, current);
    daInput.value = da !== null ? formatForInput(da) : "";
    aInput.value = a !== null ? formatForInput(a) : "";
  }

  passiStrumento(session.name)
    .then((body) => {
      obiettivoInput.value = formatForInput(body.obiettivo_sfruttamento ?? 1);
    })
    .catch(() => {
      obiettivoInput.value = "1";
    });

  campoSelect.addEventListener("change", () => {
    const field = numericFields.find((f) => f.name === campoSelect.value);
    if (field) applyPrefill(field);
  });
  applyPrefill(initialField);

  function renderResult() {
    clear(resultHost);
    if (!lastResponse) return;
    const field = numericFields.find((f) => f.name === campoSelect.value);
    const obiettivo = parseDecimal(obiettivoInput.value);
    const soloEsitoNomi = new Set(lastResponse.verifiche_solo_esito || []);
    const conEta = (lastResponse.verifiche || []).filter((v) => !soloEsitoNomi.has(v.nome));
    const soloEsito = (lastResponse.verifiche || []).filter((v) => soloEsitoNomi.has(v.nome));
    const top = selectedKeys ? conEta.filter((v) => selectedKeys.has(v.nome)) : selectTopChecks(conEta);
    const rows = buildRows(lastResponse.valori, top);
    const current = session.lastValues ? session.lastValues[field.name] : undefined;
    const chartHost = el("div", { class: "sv-chart" });
    resultHost.append(chartHost);
    renderChart(chartHost, {
      rows,
      chart: { x: "x", x_label: `${field.symbol || field.label} [${formatUnit(field.unit || "")}]`, y_label: "η" },
      series: buildSeries(top),
      guides: buildGuides(current),
      hGuides: buildHGuides(obiettivo),
      yMax: ETA_MAX_GRAFICO,
    });

    const checksHost = el("div", { class: "sv-checks", role: "group", "aria-label": "Verifiche mostrate" });
    for (const check of conEta) {
      const checked = top.some((t) => t.nome === check.nome);
      const disabled = !checked && top.length >= MAX_SERIE;
      const id = `sv-chk-${check.nome.replace(/\s+/g, "-")}`;
      const box = el("input", { type: "checkbox", id, checked, "aria-disabled": disabled });
      box.disabled = disabled;
      box.addEventListener("change", () => {
        const keys = new Set(top.map((t) => t.nome));
        if (box.checked) keys.add(check.nome);
        else keys.delete(check.nome);
        selectedKeys = keys;
        renderResult();
      });
      const label = el("label", { for: id, text: disabled ? `${check.nome} (massimo ${MAX_SERIE} verifiche)` : check.nome });
      checksHost.append(el("div", { class: "sv-check-item" }, [box, label]));
    }
    resultHost.append(checksHost);
    resultHost.append(
      buildTabella({
        valori: lastResponse.valori,
        checks: top,
        soloEsito,
        errori: lastResponse.errori,
        onUsa: (valore) => applyValue(field.name, valore),
      }),
    );
    if (!lastResponse.completa) {
      resultHost.append(el("p", { class: "sv-parziale", text: "Serie parziale: il limite di tempo ha interrotto il calcolo." }));
    }
  }

  function runCalcola() {
    const field = numericFields.find((f) => f.name === campoSelect.value);
    const body = {
      inputs: session.lastValues || {},
      campo: field.name,
      da: parseDecimal(daInput.value),
      a: parseDecimal(aInput.value),
      punti: Math.round(parseDecimal(puntiInput.value) ?? 21),
    };
    busyEl.hidden = false;
    liveRegion.textContent = "Ricerca in corso…";
    clear(resultHost);
    postSensibilita(session.name, body)
      .then((result) => {
        busyEl.hidden = true;
        if (!result.ok) {
          const message = (result.body && result.body.errors && result.body.errors[0]) || "Impossibile completare il calcolo.";
          resultHost.append(el("p", { class: "sv-errore", role: "alert", text: message }));
          liveRegion.textContent = message;
          return;
        }
        lastResponse = result.body;
        selectedKeys = null;
        renderResult();
        liveRegion.textContent = "Studio di sensibilità pronto.";
      })
      .catch(() => {
        busyEl.hidden = true;
        resultHost.append(el("p", { class: "sv-errore", role: "alert", text: "Impossibile contattare il server." }));
      });
  }
  calcolaBtn.onclick = runCalcola;
  form.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key === "Enter") {
      event.preventDefault();
      event.stopPropagation();
      runCalcola();
    }
  });

  document.body.classList.add("sv-open");
  release = trapFocus(panel, { onEscape: close });
  campoSelect.focus();
}
