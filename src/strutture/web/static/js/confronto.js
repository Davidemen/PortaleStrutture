// "Confronta con Excel" (WORKBENCH_SPEC §13.3): a results-toolbar toggle (js/results-toolbar.js
// builds `.cf-toggle` only when the tool's input schema has `legacy_compat`, js/results.js decides
// that) that mounts a panel right under the Sintesi. On: every `strutture:run-request` (the SAME
// debounced/queued trigger live calculation itself listens to, js/live.js) also fires a
// `POST .../compare` with the same valid inputs; a non-live tool only ever dispatches that event
// on "Calcola", so the toggle naturally follows the same rule there too -- nothing here has to
// special-case it. Off: the panel is removed. Never part of the printed report (js/relazione*.js
// never reads this module).
import { el, clear } from "./dom.js";
import { describeOutput, indexScalarPaths } from "./output-schema.js";
import { formatNumber, formatValue, formatUnit, formatCount } from "./format.js";
import { symbolNode } from "./symbols.js";
import { checkMark, displayCheckName } from "./verdict.js";
import { fetchCompare } from "./confronto-api.js";

function initialSession() {
  return { name: null, outputIndex: new Map(), enabled: false, lastValues: null, panel: null, summaryEl: null, bodyEl: null, seq: 0 };
}
let session = initialSession();

function stripRowIndex(percorso) {
  const indices = [...percorso.matchAll(/\[(\d+)\]/g)].map((match) => Number(match[1]) + 1);
  return { stripped: percorso.replace(/\[\d+\]/g, ""), indices };
}

// "Grandezza" cell (WORKBENCH_SPEC §13.3): symbol + label resolved via the output schema; a row
// index in the runtime path ("righe[2].eta") becomes " · riga 3", the schema itself has no notion
// of rows.
function pathCell(percorso, outputIndex) {
  const { stripped, indices } = stripRowIndex(percorso);
  const node = outputIndex.get(stripped);
  const cell = el("span", { class: "cf-path" });
  if (node && node.symbol) cell.append(symbolNode(node.symbol), " ");
  cell.append(document.createTextNode(node ? node.label : stripped));
  if (indices.length > 0) cell.append(document.createTextNode(` · riga ${indices[indices.length - 1]}`));
  return cell;
}

function valueText(value, node) {
  if (value === null || value === undefined) return "—";
  const { text } = formatValue(value, node || {});
  const unit = node && node.unit && node.unit !== "-" ? ` ${formatUnit(node.unit)}` : "";
  return `${text}${unit}`;
}

function verdictCell(label, esito) {
  const cell = el("span", { class: "cf-check-verdict" });
  cell.append(el("span", { class: "cf-check-verdict-label", text: `${label}: ` }));
  if (!esito) {
    cell.append(document.createTextNode("—"));
    return cell;
  }
  cell.append(checkMark(esito.passed));
  cell.append(document.createTextNode(esito.passed ? " Soddisfatta" : " Non soddisfatta"));
  if (typeof esito.value === "number") cell.append(document.createTextNode(` (${formatNumber(esito.value)})`));
  return cell;
}

function buildCheckDiffRow(item) {
  return el("div", { class: "cf-check" }, [
    el("span", { class: "cf-check-name", text: displayCheckName(item.nome) }),
    verdictCell("Standard", item.standard),
    verdictCell("Excel", item.excel),
  ]);
}

function buildDiffTable(differenze, outputIndex) {
  const headRow = el("tr", {}, ["Grandezza", "Standard", "Excel", "Δ", "Δ %", "Correzione"].map((text) => el("th", { text })));
  const tbody = el("tbody");
  let hasUnattributed = false;
  for (const diff of differenze) {
    const { stripped } = stripRowIndex(diff.percorso);
    const node = outputIndex.get(stripped);
    const correzioneCell = el("td", { class: "cf-correzione" });
    if (diff.divergenze.length === 0) {
      hasUnattributed = true;
      correzioneCell.textContent = "—";
    } else {
      diff.divergenze.forEach((id, index) => {
        if (index > 0) correzioneCell.append(", ");
        correzioneCell.append(el("a", { href: `#/registro?id=${encodeURIComponent(id)}`, text: id }));
      });
    }
    tbody.append(
      el("tr", {}, [
        el("td", {}, [pathCell(diff.percorso, outputIndex)]),
        el("td", { class: "cf-num", text: valueText(diff.standard, node) }),
        el("td", { class: "cf-num", text: valueText(diff.excel, node) }),
        el("td", { class: "cf-num", text: diff.delta === null || diff.delta === undefined ? "—" : formatNumber(diff.delta) }),
        el("td", { class: "cf-num", text: diff.delta_rel === null || diff.delta_rel === undefined ? "—" : `${formatNumber(diff.delta_rel * 100)}%` }),
        correzioneCell,
      ])
    );
  }
  const table = el("table", { class: "cf-table" }, [el("thead", {}, [headRow]), tbody]);
  return { table, hasUnattributed };
}

function summarySentence(confronto) {
  if (confronto.totale_differenze === 0 && confronto.verifiche.length === 0) {
    return "Nessuna differenza: per questi dati le due modalità coincidono.";
  }
  // Two different kinds of news about a check: its VERDICT differs between the modes (what the
  // engineer must know first), or only its utilisation moves while the verdict stands. The sentence
  // used to call both "cambiano esito" -- on muro-sostegno that read "12 verifiche cambiano esito"
  // next to twelve rows that were "Soddisfatta" in both modes.
  const esito = confronto.verifiche.filter((v) => v.cambia_esito).length;
  const soloValore = confronto.verifiche.length - esito;
  return [
    formatCount(confronto.totale_differenze, "valore diverso", "valori diversi"),
    esito > 0
      ? formatCount(esito, "verifica cambia esito", "verifiche cambiano esito")
      : "nessuna verifica cambia esito",
    ...(soloValore > 0 ? [formatCount(soloValore, "verifica con valore diverso", "verifiche con valore diverso")] : []),
    formatCount(confronto.divergenze_coinvolte.length, "correzione coinvolta", "correzioni coinvolte"),
  ].join(" · ");
}

// A long list is folded behind a native <details> (keyboard accessible, no script): the comparison
// sits between the Sintesi and the results, and must never push them a screen or two down.
const OPEN_UP_TO_ROWS = 8;

function foldable(label, count, content) {
  const details = el("details", { class: "cf-fold" }, [el("summary", { class: "cf-fold-summary", text: `${label} (${count})` }), content]);
  details.open = count <= OPEN_UP_TO_ROWS;
  return details;
}

function modeFailureSentence(body) {
  if (body.standard && !body.standard.ok) {
    return `Confronto non disponibile: la modalità standard non calcola questi dati — ${(body.standard.errors && body.standard.errors[0]) || "errore sconosciuto"}`;
  }
  if (body.excel && !body.excel.ok) {
    return `Confronto non disponibile: la modalità foglio Excel non calcola questi dati — ${(body.excel.errors && body.excel.errors[0]) || "errore sconosciuto"}`;
  }
  return "Confronto non disponibile per questi dati.";
}

function buildPanelShell() {
  const summaryEl = el("p", { class: "cf-summary" });
  const bodyEl = el("div", { class: "cf-body" });
  const panel = el("section", { class: "cf-panel", id: "confronto-panel", "aria-label": "Confronto con il foglio Excel" }, [
    el("h3", { class: "cf-title", text: "Confronto con il foglio Excel" }),
    summaryEl,
    bodyEl,
  ]);
  return { panel, summaryEl, bodyEl };
}

function unmountPanel() {
  if (session.panel) session.panel.remove();
  session = { ...session, panel: null, summaryEl: null, bodyEl: null };
}

function mountPanel() {
  const sintesiRoot = document.getElementById("sintesi");
  if (!sintesiRoot || !sintesiRoot.parentNode) return;
  const { panel, summaryEl, bodyEl } = buildPanelShell();
  sintesiRoot.after(panel);
  session = { ...session, panel, summaryEl, bodyEl };
}

function renderLoading() {
  if (!session.panel) return;
  session.panel.classList.add("cf-panel--stale");
  if (!session.panel.dataset.everLoaded) session.summaryEl.textContent = "Confronto in corso…";
}

function renderResult(body) {
  if (!session.panel) return;
  session.panel.classList.remove("cf-panel--stale");
  session.panel.dataset.everLoaded = "true";
  clear(session.bodyEl);
  if (!body.disponibile || !body.confronto) {
    session.summaryEl.textContent = "Confronto non disponibile per questo strumento.";
    return;
  }
  const confronto = body.confronto;
  if (!confronto.confrontabile) {
    session.summaryEl.textContent = modeFailureSentence(body);
    return;
  }
  session.summaryEl.textContent = summarySentence(confronto);
  const cambianoEsito = confronto.verifiche.filter((v) => v.cambia_esito);
  const soloValore = confronto.verifiche.filter((v) => !v.cambia_esito);
  if (cambianoEsito.length > 0) {
    // never folded: a verdict that differs between the two modes is the headline of the comparison
    session.bodyEl.append(el("div", { class: "cf-checks cf-checks--esito" }, cambianoEsito.map(buildCheckDiffRow)));
  }
  if (soloValore.length > 0) {
    session.bodyEl.append(foldable("Verifiche con valore diverso, stesso esito", soloValore.length,
      el("div", { class: "cf-checks" }, soloValore.map(buildCheckDiffRow))));
  }
  if (confronto.differenze.length > 0) {
    const { table, hasUnattributed } = buildDiffTable(confronto.differenze, session.outputIndex);
    session.bodyEl.append(foldable("Valori diversi", confronto.totale_differenze, el("div", { class: "cf-table-scroll" }, [table])));
    if (confronto.totale_differenze > confronto.differenze.length) {
      session.bodyEl.append(el("p", { class: "cf-note", text: `Mostrate le prime ${confronto.differenze.length} di ${confronto.totale_differenze}.` }));
    }
    if (hasUnattributed) {
      session.bodyEl.append(el("p", { class: "cf-note", text: "Le differenze senza correzione indicata dipendono da una correzione a monte." }));
    }
  }
  appendAttributionNotes(session.bodyEl, confronto.attribuzione);
}

// Attribution notes (WORKBENCH_SPEC §13.3 addendum): `attribuzione` is exact for the CURRENT
// inputs (the server re-runs the tool once per correction, `confronto.py::attribuisci_per_
// singola_correzione`, under its own 3s budget) -- these two lines are its own honesty checks,
// distinct from a plain unattributed ROW (`hasUnattributed` above, which is about the register's
// static `uscite` coverage, not this per-request attempt).
function appendAttributionNotes(bodyEl, attribuzione) {
  if (!attribuzione) return;
  if (attribuzione.completa === false) {
    bodyEl.append(el("p", { class: "cf-note", text: "Attribuzione parziale: non tutte le correzioni sono state provate." }));
  }
  if (attribuzione.non_valutabili && attribuzione.non_valutabili.length > 0) {
    const note = el("p", { class: "cf-note" }, [document.createTextNode("Correzioni che non si possono isolare: ")]);
    attribuzione.non_valutabili.forEach((id, index) => {
      if (index > 0) note.append(", ");
      note.append(el("a", { href: `#/registro?id=${encodeURIComponent(id)}`, text: id }));
    });
    bodyEl.append(note);
  }
}

function renderError(message) {
  if (!session.panel) return;
  session.panel.classList.remove("cf-panel--stale");
  session.panel.dataset.everLoaded = "true";
  clear(session.bodyEl);
  session.summaryEl.textContent = message;
}

// Sequence-gated, not aborted (same reasoning as js/live.js's own queueing): a stale response can
// still arrive after a fresher one went out, but it is dropped on arrival instead of ever painted.
function runCompare(values) {
  if (!session.name) return;
  const mySeq = session.seq + 1;
  session = { ...session, seq: mySeq };
  renderLoading();
  fetchCompare(session.name, values)
    .then((body) => {
      if (session.seq === mySeq) renderResult(body);
    })
    .catch((error) => {
      if (session.seq === mySeq) renderError((error && error.message) || "Impossibile confrontare le due modalità.");
    });
}

function syncToggle(button) {
  button.setAttribute("aria-pressed", String(session.enabled));
  button.onclick = () => {
    session = { ...session, enabled: !session.enabled };
    button.setAttribute("aria-pressed", String(session.enabled));
    if (session.enabled) {
      mountPanel();
      if (session.lastValues) runCompare(session.lastValues);
      else renderLoading();
    } else {
      unmountPanel();
    }
  };
}

document.addEventListener("strutture:tool-schema", (event) => {
  const { name, output } = event.detail || {};
  unmountPanel();
  session = { ...initialSession(), name, outputIndex: indexScalarPaths(describeOutput(output || {})) };
});

// The toolbar (results-toolbar.js) rebuilds a FRESH `.cf-toggle` node on every render (live or
// manual) -- re-applying the session's own `enabled` state here is what makes the toggle survive
// across those re-renders instead of resetting to "off" on the next keystroke.
document.addEventListener("strutture:results-rendered", () => {
  const button = document.querySelector(".cf-toggle");
  if (button) syncToggle(button);
});

document.addEventListener("strutture:run-request", (event) => {
  const { name, values } = event.detail || {};
  if (!session.name || name !== session.name) return;
  session = { ...session, lastValues: values };
  if (session.enabled) runCompare(values);
});
