// "Passi di arrotondamento per tipo di dato" and "Eccezioni per campo" (WORKBENCH_SPEC §26.8):
// the two accessible tables built from `GET /api/impostazioni/tipi` and the current form state.
import { el } from "./dom.js";
import { parseDecimal, formatForInput } from "./number-input.js";
import { eccezioniDuplicate } from "./impostazioni-modello.js";

function campiDisclosure(campi) {
  const details = el("details");
  details.append(el("summary", { text: `${campi.length} campi` }));
  const ul = el("ul");
  for (const c of campi) ul.append(el("li", { text: `${c.strumento} ${c.simbolo || ""} ${c.etichetta}` }));
  details.append(ul);
  return details;
}

export function buildTipiTable(tipiBody, state, onChange) {
  const table = el("table", { class: "im-tipi" }, [
    el("caption", { text: "Passi di arrotondamento per tipo di dato" }),
    el("thead", {}, [el("tr", {}, ["Tipo", "Unità", "Passo", "Campi"].map((text) => el("th", { text })))]),
  ]);
  const tbody = el("tbody");
  for (const tipo of tipiBody.tipi || []) {
    const input = el("input", {
      type: "text", inputmode: "decimal", "aria-label": `Passo per ${tipo.etichetta}`,
      value: formatForInput(state.passi_per_tipo[tipo.tipo] ?? ""), placeholder: "nessun passo",
    });
    input.addEventListener("input", () => {
      const value = input.value.trim();
      onChange(tipo.tipo, value === "" ? null : parseDecimal(value));
    });
    tbody.append(
      el("tr", {}, [
        el("td", { text: tipo.etichetta }),
        el("td", { text: tipo.unita }),
        el("td", {}, [input]),
        el("td", {}, [campiDisclosure(tipo.campi)]),
      ]),
    );
  }
  table.append(tbody);
  const wrap = el("div", { class: "im-section" }, [table]);
  if ((tipiBody.senza_tipo || []).length > 0) {
    wrap.append(
      el("details", { class: "im-senza-tipo" }, [
        el("summary", { text: "Campi senza tipo (angoli, forze, tensioni…): solo eccezioni per campo" }),
        campiDisclosure(tipiBody.senza_tipo),
      ]),
    );
  }
  return wrap;
}

function buildStrumentoOptions(campiPerStrumento, tools) {
  const toolTitle = new Map(tools.map((t) => [t.name, `${t.sigla} ${t.title}`]));
  return [...campiPerStrumento.keys()].map((name) => ({ value: name, text: toolTitle.get(name) || name }));
}

// One exception row: strumento select -> campo select (that tool's numeric fields) -> passo input
// -> "Rimuovi". `state.passi_per_campo` is mutated only through `onChange`/`onRemove` (immutable
// array replace), never in place.
function buildEccezioneRow(eccezione, index, { campiPerStrumento, tools, onChange, onRemove, duplicate }) {
  const strumentoOptions = buildStrumentoOptions(campiPerStrumento, tools);
  const strumentoSelect = el(
    "select", { "aria-label": "Strumento" },
    [el("option", { value: "", text: "— scegliere —" }), ...strumentoOptions.map((o) => el("option", { value: o.value, selected: o.value === eccezione.strumento, text: o.text }))],
  );
  const campoOptions = campiPerStrumento.get(eccezione.strumento) || [];
  const campoSelect = el(
    "select", { "aria-label": "Campo" },
    [el("option", { value: "", text: "— scegliere —" }), ...campoOptions.map((c) => el("option", { value: c.campo, selected: c.campo === eccezione.campo, text: `${c.simbolo || ""} ${c.etichetta}` }))],
  );
  const passoInput = el("input", { type: "text", inputmode: "decimal", "aria-label": "Passo", value: formatForInput(eccezione.passo ?? ""), placeholder: "nessun passo: chiedi ogni volta" });
  const removeBtn = el("button", { type: "button", class: "im-rimuovi", text: "✕ Rimuovi" });

  strumentoSelect.addEventListener("change", () => onChange(index, { strumento: strumentoSelect.value, campo: "" }));
  campoSelect.addEventListener("change", () => onChange(index, { campo: campoSelect.value }));
  passoInput.addEventListener("input", () => {
    const value = passoInput.value.trim();
    onChange(index, { passo: value === "" ? null : parseDecimal(value) });
  });
  removeBtn.addEventListener("click", () => onRemove(index));

  const row = el("div", { class: "im-eccezione-row" }, [strumentoSelect, campoSelect, passoInput, removeBtn]);
  if (duplicate) row.append(el("p", { class: "im-errore", role: "alert", text: "Eccezione duplicata per questo strumento e campo." }));
  return row;
}

export function buildEccezioniSection(state, { campiPerStrumento, tools, onChange, onRemove, onAdd }) {
  const wrap = el("div", { class: "im-section im-eccezioni" });
  wrap.append(el("h3", { text: "Eccezioni per campo" }));
  const duplicati = eccezioniDuplicate(state.passi_per_campo);
  const list = el("div", { class: "im-eccezioni-list" });
  state.passi_per_campo.forEach((eccezione, index) => {
    list.append(buildEccezioneRow(eccezione, index, { campiPerStrumento, tools, onChange, onRemove, duplicate: duplicati.has(index) }));
  });
  wrap.append(list);
  const addBtn = el("button", { type: "button", class: "im-aggiungi", text: "+ Aggiungi eccezione" });
  addBtn.addEventListener("click", onAdd);
  wrap.append(addBtn);
  return wrap;
}
