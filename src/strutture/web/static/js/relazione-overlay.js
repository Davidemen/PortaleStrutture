// Report personalisation overlay (WORKBENCH_SPEC §11): every entry point ("Stampa relazione" in
// the results toolbar, the Dati "⋯" menu -- which just re-clicks the same button, forms.js -- and
// Ctrl/Cmd+P) opens this full-window `<dialog>` instead of printing straight away. A native modal
// `<dialog>` (`showModal()`, same pattern as js/midas-dialog.js) makes the background `inert` for
// free -- the underlying form cannot change while the overlay is open, so the stale-results check
// only ever needs to run once, at open time. Its OWN Tab-wrapping is not fully reliable once the
// dialog's last focusable descendant is reached (observed: focus can land on `<body>` instead of
// cycling back), so `trapFocus` (nav-state.js, already used by the palette/shortcuts dialogs) is
// layered on top for a real, WCAG-conformant trap; Escape is handled explicitly through it too
// rather than the native default, so both paths close the SAME way.
import { el, clear } from "./dom.js";
import { getReportState } from "./results.js";
import { trapFocus } from "./nav-state.js";
import { resolveReportForPrint, ensurePrintRoot, buildPrintDocument, showRefusal, clearRefusal } from "./relazione-print.js";
import {
  resolveOptions,
  loadContents,
  saveContents,
  cartiglioFields,
  saveCartiglio,
  effectiveCartiglio,
  applyPreset,
  editSezioni,
  editGruppo,
  editTabelle,
  editPagina,
} from "./relazione-options.js";
import { buildCartiglioFieldset } from "./relazione-overlay-cartiglio.js";
import { buildContenutoFieldset } from "./relazione-overlay-contenuto.js";
import { buildTabelleFieldset, buildPaginaFieldset } from "./relazione-overlay-pagina.js";
import { schedulePreviewUpdate } from "./relazione-preview.js";

let dialogEl = null;
let session = null;

function todayIsoLocal() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

function printOptions() {
  return { ...session.resolved, cartiglio: effectiveCartiglio(session.cartiglioRaw, session.toolTitle) };
}

function updatePreview({ immediate = false } = {}) {
  if (!session) return;
  schedulePreviewUpdate(
    { pagesHost: session.elements.pages, indicatorEl: session.elements.indicator, scrollHost: session.elements.pages },
    { tool: session.tool, report: session.report, options: printOptions() },
    { immediate },
  );
}

function persistContents() {
  const { cartiglio, ...contents } = session.resolved; // sm.cartiglio owns cartiglio, not this key
  saveContents(session.toolName, contents);
}

function renderOptionsPane() {
  const pane = session.elements.optionsPane;
  clear(pane);
  pane.append(
    el("div", { class: "rel-options-toolbar" }, [
      el("button", { type: "button", class: "rel-btn-reset", text: "Ripristina predefiniti", onclick: resetDefaults }),
    ]),
  );
  pane.append(
    buildCartiglioFieldset(session.cartiglioRaw, {
      toolTitle: session.toolTitle,
      todayIso: todayIsoLocal(),
      onChange: (key, value) => {
        session.cartiglioRaw = { ...session.cartiglioRaw, [key]: value };
        saveCartiglio(session.cartiglioRaw);
        updatePreview();
      },
    }),
  );
  pane.append(
    buildContenutoFieldset(session.resolved, {
      outputNodes: session.outputNodes,
      onPreset: (preset) => applyChange(applyPreset(preset, session.resolved, session.outputNodes)),
      onSezione: (patch) => applyChange(editSezioni(session.resolved, patch)),
      onGruppo: (path, included) => applyChange(editGruppo(session.resolved, path, included)),
    }),
  );
  pane.append(
    buildTabelleFieldset(session.resolved.tabelle, {
      onRighe: (righe) => applyChange(editTabelle(session.resolved, { righe })),
      onN: (n) => {
        session.resolved = editTabelle(session.resolved, { n });
        persistContents();
        updatePreview();
      },
    }),
  );
  pane.append(
    buildPaginaFieldset(session.resolved.pagina, {
      onOrientamento: (orientamento) => applyLeaf(editPagina(session.resolved, { orientamento })),
      onCorpo: (corpo) => applyLeaf(editPagina(session.resolved, { corpo })),
      onNumeri: (numeri) => applyLeaf(editPagina(session.resolved, { numeri })),
      onIntestazione: (intestazione) => applyLeaf(editPagina(session.resolved, { intestazione })),
    }),
  );
}

// A change that can affect ANOTHER control's enabled/checked state (preset, any Contenuto
// checkbox, the Tabelle row policy) -- rebuilds the whole pane so it never drifts out of sync.
function applyChange(nextResolved) {
  session.resolved = nextResolved;
  persistContents();
  renderOptionsPane();
  updatePreview();
}

// A leaf change (Pagina's own controls, Tabelle's "N" field) nothing else depends on -- state +
// preview only, no pane rebuild (keeps focus/cursor position in the field being edited).
function applyLeaf(nextResolved) {
  session.resolved = nextResolved;
  persistContents();
  updatePreview();
}

function resetDefaults() {
  session.resolved = resolveOptions({});
  session.cartiglioRaw = {};
  saveCartiglio(session.cartiglioRaw);
  persistContents();
  renderOptionsPane();
  updatePreview();
}

function setMobileTab(tab) {
  dialogEl.dataset.view = tab;
  for (const button of dialogEl.querySelectorAll(".rel-tab")) button.setAttribute("aria-selected", String(button.dataset.tab === tab));
}

// Orientation/compact body (WORKBENCH_SPEC §11 "Pagina") are chosen via a class on <html>, read by
// the named `@page` rule in css/print.css -- cleared again on `afterprint` (below) so a later
// browser-menu print (the `beforeprint` FALLBACK in relazione-print.js, always the complete
// portrait/normal report) is never left in landscape/compact from a previous overlay session.
function applyPageClasses(pagina) {
  document.documentElement.classList.toggle("rel-print-landscape", pagina.orientamento === "orizzontale");
  document.documentElement.classList.toggle("rel-print-compact", pagina.corpo === "compatto");
}

function handleOverlayPrint() {
  const options = printOptions();
  const root = ensurePrintRoot();
  clear(root);
  buildPrintDocument(root, { tool: session.tool, report: session.report }, options);
  root.dataset.fresh = "true";
  applyPageClasses(options.pagina);
  window.print();
}

window.addEventListener("afterprint", () => {
  document.documentElement.classList.remove("rel-print-landscape", "rel-print-compact");
});

function buildHeader(trigger) {
  const tabs = el("div", { class: "rel-overlay-tabs", role: "tablist", "aria-label": "Vista" }, [
    el("button", { type: "button", class: "rel-tab", "data-tab": "opzioni", role: "tab", "aria-selected": "true", text: "Opzioni", onclick: () => setMobileTab("opzioni") }),
    el("button", { type: "button", class: "rel-tab", "data-tab": "anteprima", role: "tab", "aria-selected": "false", text: "Anteprima", onclick: () => setMobileTab("anteprima") }),
  ]);
  const actions = el("div", { class: "rel-overlay-actions" }, [
    el("button", { type: "button", class: "rel-btn-cancel", text: "Annulla", onclick: () => dialogEl.close() }),
    el("button", { type: "button", class: "rel-btn-print", text: "Stampa / Salva PDF", onclick: handleOverlayPrint }),
  ]);
  return el("header", { class: "rel-overlay-header" }, [el("h2", { id: "rel-overlay-title", tabindex: "-1", text: "Relazione di calcolo" }), tabs, actions]);
}

function buildDialog(trigger) {
  const optionsPane = el("div", { id: "rel-options-pane", class: "rel-options-pane" });
  const pages = el("div", { class: "rel-preview-pages" });
  const indicator = el("p", { class: "rel-page-indicator", "aria-live": "polite" });
  const previewPane = el("div", { id: "rel-preview-pane", class: "rel-preview-pane" }, [
    el("h3", { class: "rel-preview-title", text: "Anteprima" }),
    pages,
    indicator,
  ]);
  const body = el("div", { class: "rel-overlay-body" }, [optionsPane, previewPane]);
  const dialog = el("dialog", { id: "relazione-overlay", class: "rel-overlay", role: "dialog", "aria-modal": "true", "aria-labelledby": "rel-overlay-title" }, [
    buildHeader(trigger),
    body,
  ]);
  dialog.dataset.view = "opzioni";
  session.elements = { optionsPane, pages, indicator };
  return dialog;
}

let releaseFocusTrap = null;

function handleClose() {
  document.body.classList.remove("rel-scroll-lock");
  if (releaseFocusTrap) {
    releaseFocusTrap(); // restores focus to the trigger (WORKBENCH_SPEC §11 "Esc/Annulla... returns focus to the trigger")
    releaseFocusTrap = null;
  }
  dialogEl.remove();
  dialogEl = null;
  session = null;
}

async function openOverlay(trigger) {
  if (dialogEl) return;
  const before = getReportState();
  if (!before.tool) return;
  clearRefusal();
  const report = await resolveReportForPrint(before);
  const state = { ...getReportState(), report };
  if (!report || !state.tool) {
    showRefusal();
    return;
  }
  const toolName = state.tool.name;
  const outputNodes = state.tool.outputNodes || [];
  session = {
    toolName,
    toolTitle: state.tool.title,
    outputNodes,
    tool: state.tool,
    report: state.report,
    resolved: resolveOptions(loadContents(toolName) || {}),
    cartiglioRaw: cartiglioFields(),
    trigger,
  };
  dialogEl = buildDialog(trigger);
  document.body.append(dialogEl);
  dialogEl.addEventListener("close", handleClose);
  renderOptionsPane();
  // `previous` (trapFocus, captured HERE, before showModal() moves focus into the dialog) is
  // `trigger` itself -- installed before `showModal()` on purpose, and Escape routed through it
  // explicitly (`dialogEl.close()`, which fires the SAME "close" -> `handleClose` either way) so
  // native `<dialog>` Tab-wrapping (unreliable once the last focusable descendant is reached,
  // observed landing on `<body>`) is never the only thing keeping focus inside the modal.
  releaseFocusTrap = trapFocus(dialogEl, { onEscape: () => dialogEl.close() });
  dialogEl.showModal();
  document.body.classList.add("rel-scroll-lock");
  updatePreview({ immediate: true });
}

document.addEventListener("click", (event) => {
  const trigger = event.target.closest(".r-print-trigger");
  if (!trigger) return;
  event.preventDefault();
  openOverlay(trigger);
});

document.addEventListener("keydown", (event) => {
  if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "p") return;
  if (!getReportState().tool) return;
  event.preventDefault();
  if (dialogEl) handleOverlayPrint();
  else openOverlay(document.querySelector(".r-print-trigger") || document.body);
});
