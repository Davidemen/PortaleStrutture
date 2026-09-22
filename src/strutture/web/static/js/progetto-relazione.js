// "Relazione di progetto" (WORKBENCH_SPEC §14.3): the personalisation overlay (§11) ONCE for the
// whole set -- Contenuto/Tabelle/Pagina only (no per-tool "Risultati" group list: elements can
// have different tools, and no Cartiglio fieldset either -- the project/element cartiglios below
// are fixed, built straight from the project/element records, never freeform §11 text) -- then ONE
// print document: a project cartiglio, then every element in list order as its own section, built
// from a FRESH run of its stored inputs (`?relazione=1` when "Sviluppo dei calcoli" is on AND that
// element's own tool supports it). A run that fails prints its Italian error instead of results;
// an unknown tool prints "Strumento non disponibile in questa versione".
import { el, clear } from "./dom.js";
import { trapFocus } from "./nav-state.js";
import { fetchTools, fetchSchema } from "./api.js";
import { describeFields } from "./schema.js";
import { describeOutput } from "./output-schema.js";
import { fetchElementi } from "./progetti-api.js";
import { runToolForPrint, ensurePrintRoot } from "./relazione-print.js";
import { buildRelazione, resolveOptions } from "./relazione.js";
import { formatIsoDateIt, applyPreset } from "./relazione-options.js";
import { buildContenutoFieldset } from "./relazione-overlay-contenuto.js";
import { buildTabelleFieldset, buildPaginaFieldset } from "./relazione-overlay-pagina.js";
import { STATO_LABELS } from "./progetto-elementi.js";

function todayIsoLocal() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

function formatDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" });
}

function metaSection(entries, extraClass) {
  const section = el("section", { class: `print-cartiglio${extraClass ? ` ${extraClass}` : ""}` });
  const meta = el("dl", { class: "print-cartiglio-meta" });
  for (const [term, value] of entries) {
    if (!value) continue;
    meta.append(el("dt", { text: term }), el("dd", { text: value }));
  }
  section.append(meta);
  return section;
}

function buildProgettoCartiglio(progetto, elementiCount) {
  const cartiglio = metaSection([
    ["Codice", progetto.codice],
    ["Progetto", progetto.nome],
    ["Committente", progetto.committente],
    ["Data", formatIsoDateIt(todayIsoLocal())],
    ["N. elementi", String(elementiCount)],
  ]);
  return el("div", { class: "print-progetto-cartiglio" }, [el("h1", { text: "Relazione di progetto" }), cartiglio]);
}

function buildElementoCartiglio(elemento, schema) {
  return metaSection([
    ["Elemento", elemento.nome],
    ["Sigla", schema ? schema.sigla : ""],
    ["Strumento", schema ? schema.title : `${elemento.strumento} (non disponibile)`],
    ["Stato", STATO_LABELS[elemento.stato] || elemento.stato],
    ["Aggiornato", formatDate(elemento.aggiornato)],
  ]);
}

// One element's printed section: sub-cartiglio + either the full §10 report (fresh run), the
// element's own run error, or the unknown-tool notice. Never throws -- every failure mode ends in
// a printed paragraph instead, so one bad element can never blank out the rest of the document.
// `knownTools` (fetched ONCE, `GET /api/tools`, never 404s) is checked BEFORE ever requesting a
// schema -- js/main.js's own `selectTool` uses the exact same "check the list first" pattern to
// decide `showUnknownTool` for the same reason: a `fetchSchema()` call for a name already known to
// be absent would 404, and Chrome logs "Failed to load resource" for that unconditionally, THROUGH
// the try/catch below -- a console error this module can catch in JS but can never suppress at the
// network-log level, which the acceptance bar for this feature (no console errors while printing)
// does not allow.
async function buildElementoSezione(elemento, resolved, index, knownTools) {
  const body = el("div", { class: "print-elemento-body" });
  if (!knownTools.has(elemento.strumento)) {
    body.append(el("p", { class: "print-omessi", text: "Strumento non disponibile in questa versione" }));
    return el("section", { class: "print-elemento-sezione", "data-index": String(index) }, [buildElementoCartiglio(elemento, null), body]);
  }
  let schema = null;
  try {
    schema = await fetchSchema(elemento.strumento);
  } catch (error) {
    body.append(el("p", { class: "print-omessi", text: "Strumento non disponibile in questa versione" }));
    return el("section", { class: "print-elemento-sezione", "data-index": String(index) }, [buildElementoCartiglio(elemento, null), body]);
  }
  const wantsTraccia = Boolean(resolved.sezioni.sviluppo) && Boolean(schema.relazione);
  let report;
  try {
    const result = await runToolForPrint(elemento.strumento, elemento.inputs || {}, wantsTraccia);
    report = result.report;
  } catch (error) {
    report = null;
  }
  if (!report || report.ok === false) {
    const message = (report && Array.isArray(report.errors) && report.errors[0]) || "Impossibile calcolare l'elemento.";
    body.append(el("p", { class: "print-omessi", text: message }));
  } else {
    const fields = describeFields(schema.input || {});
    const outputNodes = describeOutput(schema.output || {});
    const tool = { name: elemento.strumento, title: schema.title, norm: schema.norm, relazione: Boolean(schema.relazione) };
    const elementOptions = { ...resolved, sezioni: { ...resolved.sezioni, cartiglio: false } };
    buildRelazione(body, { tool, report, outputNodes, fields }, elementOptions, `pj-${index}`);
  }
  return el("section", { class: "print-elemento-sezione", "data-index": String(index) }, [buildElementoCartiglio(elemento, schema), body]);
}

async function generateAndPrint(progetto, elementi, resolved, onProgress) {
  let knownTools = new Set();
  try {
    knownTools = new Set((await fetchTools()).map((tool) => tool.name));
  } catch (error) {
    // every element prints "Strumento non disponibile" rather than the app guessing -- a report
    // is still generated, just a conservative one, and the SAME `fetchTools()` failure would have
    // stopped the whole page (rail, Home, palette) from ever getting this far in the first place
  }
  const root = ensurePrintRoot();
  clear(root);
  root.append(buildProgettoCartiglio(progetto, elementi.length));
  // Sequential on purpose: each element is a real, independent fresh run -- running them in
  // parallel would flood the server with N simultaneous tool executions for what is already a
  // rare, deliberate, one-at-a-time "print everything" action, and the progress line ("Elemento 3
  // di 12...") only means something if they finish in that same order.
  for (let index = 0; index < elementi.length; index += 1) {
    onProgress(index + 1, elementi.length);
    const section = await buildElementoSezione(elementi[index], resolved, index, knownTools);
    root.append(section);
  }
  root.dataset.fresh = "true";
  window.print();
}

let dialogEl = null;
let releaseTrap = null;

function closeDialog() {
  if (releaseTrap) {
    releaseTrap();
    releaseTrap = null;
  }
  if (dialogEl) {
    const node = dialogEl;
    dialogEl = null;
    node.close();
    node.remove();
  }
}

export async function openRelazioneProgetto(progetto) {
  closeDialog();
  let elementi = [];
  let loadError = "";
  try {
    elementi = await fetchElementi(progetto.id);
  } catch (error) {
    loadError = error.message || "Impossibile caricare gli elementi del progetto.";
  }

  let resolved = resolveOptions({});
  const titleId = "pr-dialog-title";
  const optionsPane = el("div", { class: "rel-options-pane pr-options-pane" });
  const progressEl = el("p", { class: "pr-progress", role: "status", "aria-live": "polite" });
  progressEl.hidden = true;
  const generateBtn = el("button", { type: "button", class: "rel-btn-print", text: "Genera e stampa" });
  const cancelBtn = el("button", { type: "button", class: "rel-btn-cancel", text: "Annulla", onclick: closeDialog });

  function renderOptionsPane() {
    clear(optionsPane);
    optionsPane.append(
      buildContenutoFieldset(resolved, {
        outputNodes: [],
        hasFormule: true,
        onPreset: (preset) => {
          resolved = applyPreset(preset, resolved, []);
          renderOptionsPane();
        },
        onSezione: (patch) => {
          resolved = resolveOptions({ ...resolved, sezioni: { ...resolved.sezioni, ...patch } });
          renderOptionsPane();
        },
        onGruppo: () => {},
      }),
    );
    optionsPane.append(
      buildTabelleFieldset(resolved.tabelle, {
        onRighe: (righe) => {
          resolved = resolveOptions({ ...resolved, tabelle: { ...resolved.tabelle, righe } });
          renderOptionsPane();
        },
        onN: (n) => {
          resolved = resolveOptions({ ...resolved, tabelle: { ...resolved.tabelle, n } });
        },
      }),
    );
    optionsPane.append(
      buildPaginaFieldset(resolved.pagina, {
        onOrientamento: (orientamento) => { resolved = resolveOptions({ ...resolved, pagina: { ...resolved.pagina, orientamento } }); },
        onCorpo: (corpo) => { resolved = resolveOptions({ ...resolved, pagina: { ...resolved.pagina, corpo } }); },
        onNumeri: (numeri) => { resolved = resolveOptions({ ...resolved, pagina: { ...resolved.pagina, numeri } }); },
        onIntestazione: (intestazione) => { resolved = resolveOptions({ ...resolved, pagina: { ...resolved.pagina, intestazione } }); },
      }),
    );
  }
  renderOptionsPane();

  generateBtn.addEventListener("click", async () => {
    generateBtn.disabled = true;
    cancelBtn.disabled = true;
    optionsPane.hidden = true;
    progressEl.hidden = false;
    document.documentElement.classList.toggle("rel-print-landscape", resolved.pagina.orientamento === "orizzontale");
    document.documentElement.classList.toggle("rel-print-compact", resolved.pagina.corpo === "compatto");
    try {
      await generateAndPrint(progetto, elementi, resolved, (done, total) => {
        progressEl.textContent = `Elemento ${done} di ${total}…`;
      });
    } finally {
      closeDialog();
    }
  });

  const body = el("div", { class: "rel-overlay-body pr-overlay-body" }, [optionsPane, progressEl]);
  dialogEl = el("dialog", { class: "rel-overlay pr-overlay", role: "dialog", "aria-modal": "true", "aria-labelledby": titleId }, [
    el("header", { class: "rel-overlay-header" }, [
      el("h2", { id: titleId, text: "Relazione di progetto" }),
      el("div", { class: "rel-overlay-actions" }, [cancelBtn, generateBtn]),
    ]),
    loadError
      ? el("p", { class: "pr-dialog-error", role: "alert", text: loadError })
      : el("p", { class: "pr-count", text: `${elementi.length} elemento${elementi.length === 1 ? "" : "i"} in questo progetto.` }),
    body,
  ]);
  document.body.append(dialogEl);
  dialogEl.addEventListener("close", closeDialog);
  releaseTrap = trapFocus(dialogEl, { onEscape: closeDialog });
  dialogEl.showModal();
}

window.addEventListener("afterprint", () => {
  document.documentElement.classList.remove("rel-print-landscape", "rel-print-compact");
});
