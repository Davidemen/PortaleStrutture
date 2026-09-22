// "Salva in progetto" (WORKBENCH_SPEC §14.1): the Dati action-bar widget (button + header-state
// text), its create/"Salva come nuovo" dialog, the 409 conflict dialog and the `?elemento=<id>`
// deep-link loader. Mounted directly by js/forms.js's `renderForm` (a plain function call, not an
// event listener -- `#form-actions` is rebuilt synchronously on every `strutture:tool-schema`, and
// mounting via a document-level listener of our own could race forms.js's OWN listener that clears
// the bar first) so ordering is guaranteed rather than left to dynamic-import timing.
import { el } from "./dom.js";
import { visibleValues } from "./forms-sections.js";
import { save } from "./form-state.js";
import { requestRun, whenSettled } from "./live.js";
import { getCurrentProgetto, setCurrentProgetto } from "./progetto-picker.js";
import { takeAnteprimaStash } from "./progetto-anteprima.js";
import { computeSintesiEStato } from "./elemento-sintesi.js";
import { activeProvenienza, reconstructProvenienza, aggiornaOrigini } from "./provenienza.js";
import { azzeraStoriaAnnulla } from "./annulla-ui.js";
import { apriConflittoDialog } from "./elemento-conflitto.js";
import { openCreateDialog as openCreateDialogImpl } from "./elemento-salva-dialog.js";
import { fetchProgetto, fetchElemento, updateElemento } from "./progetti-api.js";
import { caricaVarianti } from "./varianti-state.js";
import { confermaChiusuraVarianti } from "./varianti-chiusura-confirm.js";

// Module-level, same "last mount wins" pattern as js/annulla-ui.js's own `activeTool` --
// js/varianti-bar.js reads this (never writes it) to give a brand-new variant A its `origine`
// (§19.2: "when the form was opened from an element, A carries origine"). `null` whenever the
// current tool page has no loaded element at all.
let activeLoaded = null;
export function activeElementoOrigine() {
  return activeLoaded ? { elemento_id: activeLoaded.id, revisione: activeLoaded.revisione, nome: activeLoaded.nome } : null;
}

// The element payload shape POST/PUT already share (routes/progetti.py) -- extracted so
// js/varianti-tieni.js (§19.4 "Aggiorna"/"Salva come nuovo") builds the exact same body from a
// variant's own inputs/report instead of re-deriving it.
export function buildElementoPayload({ tool, values, sintesi, stato, nome, provenienza, sigla = "", nota = "" }) {
  return {
    strumento: tool,
    nome,
    inputs: values,
    sintesi,
    stato,
    modalita: values.legacy_compat ? "excel" : "standard",
    provenienza,
    sigla: sigla || "",
    nota: nota || "",
  };
}

export function mountElementoSalva({ toolForm, tool, title, fields, params, input, getApi }) {
  const wrap = el("div", { class: "es-widget" });
  const stateText = el("span", { class: "es-state-text" });
  stateText.hidden = true;
  const saveBtn = el("button", { type: "button", class: "es-btn-save", text: "Salva in progetto" });
  const saveAsNewBtn = el("button", { type: "button", class: "es-btn-save-new", text: "Salva come nuovo" });
  saveAsNewBtn.hidden = true;
  const statusEl = el("p", { class: "es-status", role: "status" });
  // No `role="alert"` here, unlike every dialog-scoped error below -- DESIGN_SPEC §3 fixes
  // EXACTLY 3 live regions app-wide, and this widget (unlike a dialog, or js/registro.js's own
  // `role="alert"`, which never coexists with a tool page's three) is mounted straight into the
  // Dati action bar of EVERY tool page, additive to its existing 3. The message still reaches an
  // AT user by being plain visible text right next to the button that produced it (js/fields.js's
  // own per-field errors use the same "visible, not live" pattern for the identical reason).
  const errorEl = el("p", { class: "es-error" });
  errorEl.hidden = true;
  wrap.append(stateText, saveBtn, saveAsNewBtn, statusEl, errorEl);

  let loaded = null; // {id, revisione, nome, sigla, nota, progettoId, progettoNome} | null
  let dialogEl = null;
  let releaseTrap = null;
  // Fingerprint of the inputs+modalita the CURRENTLY loaded element was saved/reloaded with --
  // §25.1: "Usa in..." adds `da_elemento`/`da_revisione` only when the on-screen inputs are
  // IDENTICAL to this saved revision, not merely when the last run finished (a run can finish
  // successfully on inputs that were never saved at all).
  let savedFootprint = null;
  function captureFootprint() {
    savedFootprint = JSON.stringify(visibleValues(toolForm, fields));
  }
  function isUnmodified() {
    return loaded !== null && savedFootprint === JSON.stringify(visibleValues(toolForm, fields));
  }

  function showError(message) {
    errorEl.textContent = message || "Errore imprevisto.";
    errorEl.hidden = false;
    statusEl.textContent = "";
  }
  function showStatus(message) {
    statusEl.textContent = message;
    errorEl.hidden = true;
  }

  function renderWidgetState() {
    activeLoaded = loaded;
    if (loaded) {
      stateText.hidden = false;
      stateText.textContent = `Elemento: ${loaded.nome} · ${loaded.progettoNome || ""}`;
      saveBtn.textContent = "Salva";
      saveAsNewBtn.hidden = false;
    } else {
      stateText.hidden = true;
      saveBtn.textContent = "Salva in progetto";
      saveAsNewBtn.hidden = true;
    }
  }

  function currentPayload(nome, sigla, nota) {
    const values = visibleValues(toolForm, fields);
    const { sintesi, stato } = computeSintesiEStato(tool);
    return buildElementoPayload({ tool, values, sintesi, stato, nome, provenienza: activeProvenienza(tool), sigla, nota });
  }

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

  async function doUpdate() {
    if (!loaded) return;
    saveBtn.disabled = true;
    try {
      await whenSettled(); // §20.1: the saved sintesi belongs to the saved inputs
      const body = { ...currentPayload(loaded.nome, loaded.sigla, loaded.nota), revisione: loaded.revisione };
      const result = await updateElemento(loaded.id, body);
      if (result.conflict) {
        showConflictDialog(result.attuale);
        return;
      }
      loaded = { ...loaded, revisione: result.data.revisione };
      captureFootprint();
      renderWidgetState();
      showStatus("Elemento salvato.");
    } catch (error) {
      showError(error.message);
    } finally {
      saveBtn.disabled = false;
    }
  }

  // The dialog's own DOM/wiring live in js/elemento-salva-dialog.js (§25.4: kept this module
  // under the 400-line cap) -- this wrapper supplies the caller-side state/callbacks and keeps
  // `dialogEl`/`releaseTrap` so `closeDialog()` above still works unchanged.
  async function openCreateDialog(options) {
    const mounted = await openCreateDialogImpl(
      {
        tool, title, loaded, currentPayload, closeDialog,
        onCreated: (created, targetId, targetNome, sigla, nota) => {
          loaded = { id: created.id, revisione: created.revisione, nome: created.nome, sigla, nota, progettoId: targetId, progettoNome: targetNome };
          captureFootprint();
          const current2 = getCurrentProgetto();
          if (!current2 || current2.id !== targetId) setCurrentProgetto({ id: targetId, nome: targetNome });
          renderWidgetState();
          showStatus("Elemento salvato in progetto.");
        },
      },
      options,
    );
    dialogEl = mounted.dialogEl;
    releaseTrap = mounted.releaseTrap;
  }

  async function applyReload(attuale) {
    const api = getApi();
    if (api) api.setValues(attuale.inputs || {});
    azzeraStoriaAnnulla(); // WORKBENCH_SPEC §21.1: "Ricarica" is a history boundary
    const values = visibleValues(toolForm, fields);
    // Same reasoning as loadElementoFromParams: the "da <sigla>" provenance chips must reflect
    // the RELOADED (server) inputs, not whatever the session still held from before -- otherwise
    // a following Salva registers a collegamento with a value that no longer matches the field,
    // or drops the server's own provenance entirely.
    await reconstructProvenienza({ toolForm, tool, fields, input, values, provenienza: attuale.provenienza });
    save(tool, values, fields);
    requestRun(tool, values, "manual");
    loaded = loaded ? { ...loaded, revisione: attuale.revisione, nome: attuale.nome } : loaded;
    captureFootprint();
    renderWidgetState();
    closeDialog();
    showStatus("Elemento ricaricato: le modifiche locali sono state scartate.");
  }

  function showConflictDialog(attuale) {
    closeDialog();
    apriConflittoDialog({
      attuale,
      onRicarica: applyReload,
      onSalvaCopia: () => {
        const nome = loaded ? `${loaded.nome} (copia)` : "";
        const progettoId = loaded && loaded.progettoId;
        openCreateDialog({ progettoId, defaultNome: nome });
      },
    });
  }

  saveBtn.addEventListener("click", () => {
    if (loaded) doUpdate();
    else openCreateDialog({});
  });
  saveAsNewBtn.addEventListener("click", () =>
    openCreateDialog({ progettoId: loaded && loaded.progettoId, defaultNome: loaded ? `${loaded.nome} (nuovo)` : "" }),
  );

  // `#/<tool>?anteprima=1` (§14.3, "Carica questa revisione... without saving"): fills the form
  // from the stashed revision and runs it, but never sets `loaded` -- stays in the plain "Salva in
  // progetto" state, since this preview is not tied to any element.
  async function loadAnteprimaFromParams() {
    if (!params || params.anteprima !== "1") return false;
    const stash = takeAnteprimaStash(tool);
    if (!stash) return false;
    // §19.2: an open varianti set must not be silently overwritten by a preview load -- the
    // engineer chooses "Chiudi e carica" or "Annulla" before the stash is applied.
    if (caricaVarianti(tool) && !(await confermaChiusuraVarianti(tool))) return false;
    // `getApi()` only resolves to a real value once `renderForm` (js/forms.js) has finished
    // assigning it, which -- unlike every other path below -- never happens on its own here:
    // `takeAnteprimaStash` is synchronous, so without a deliberate await this whole function would
    // still be running inside `renderForm`'s OWN synchronous call stack, before `api` exists.
    await Promise.resolve();
    const api = getApi();
    if (api) api.setValues(stash.inputs || {});
    azzeraStoriaAnnulla(); // WORKBENCH_SPEC §21.1: "?anteprima=1" is a history boundary
    const values = visibleValues(toolForm, fields);
    save(tool, values, fields);
    requestRun(tool, values, "manual");
    showStatus("Revisione caricata in anteprima: non è collegata a un elemento salvato.");
    return true;
  }

  async function loadElementoFromParams() {
    if (await loadAnteprimaFromParams()) return;
    const id = params && params.elemento;
    if (!id) return;
    // §19.2: same rule as the `?anteprima=1` path above -- an open varianti set is never
    // overwritten by an `?elemento=` load without the engineer's explicit confirmation.
    if (caricaVarianti(tool) && !(await confermaChiusuraVarianti(tool))) return;
    try {
      const elemento = await fetchElemento(id);
      const api = getApi();
      if (api) api.setValues(elemento.inputs || {});
      azzeraStoriaAnnulla(); // WORKBENCH_SPEC §21.1: "?elemento=" load is a history boundary
      const values = visibleValues(toolForm, fields);
      // §25.1: rebuild the "da <sigla>" chips AFTER the history reset above, so this restoration
      // is never itself an undoable step (undo cannot bring a chip back, by design).
      await reconstructProvenienza({ toolForm, tool, fields, input, values, provenienza: elemento.provenienza });
      save(tool, values, fields);
      requestRun(tool, values, "manual");
      // §25.4: "Aggiorna dai dati a monte" row action -- AFTER the history reset/reconstruction
      // above, so it is its own single undoable step, never entangled with the `?elemento=` load.
      if (params && params.aggiorna_origini === "1") {
        await aggiornaOrigini({ toolForm, tool, fields, input, getApi, progettoId: elemento.progetto_id, elementoId: elemento.id });
      }
      let progettoNome = "";
      try {
        progettoNome = (await fetchProgetto(elemento.progetto_id)).nome;
      } catch (error) {
        progettoNome = "";
      }
      loaded = { id: elemento.id, revisione: elemento.revisione, nome: elemento.nome, sigla: "", nota: "", progettoId: elemento.progetto_id, progettoNome };
      captureFootprint();
      setCurrentProgetto({ id: elemento.progetto_id, nome: progettoNome });
      renderWidgetState();
    } catch (error) {
      showError(error.message || "Impossibile caricare l'elemento.");
    }
  }

  renderWidgetState();
  loadElementoFromParams();

  // WORKBENCH_SPEC §25.1: js/usa-in.js reads `loadedElementState()` (below) BEFORE adding
  // `&da_elemento=&da_revisione=` to a "Usa in..." link -- only a SAVED, currently-loaded element
  // (never the transient state of an unsaved `?anteprima=1` preview, which never sets `loaded`)
  // AND whose on-screen inputs are still exactly what was saved (`isUnmodified()`) is eligible.
  // `tool` closes over this mount's own tool name so a stale reference from a previous page can
  // never answer for the wrong tool.
  currentTool = tool;
  currentLoaded = () => loaded;
  currentUnmodified = isUnmodified;

  return wrap;
}

// Module-level, like js/provenienza.js's own `session`: only one tool page is ever mounted at a
// time, so the LATEST `mountElementoSalva` call always wins.
let currentTool = null;
let currentLoaded = () => null;
let currentUnmodified = () => false;

export function loadedElementState(tool) {
  if (currentTool !== tool) return null;
  const loaded = currentLoaded();
  if (!loaded) return null;
  return { id: loaded.id, revisione: loaded.revisione, modificato: !currentUnmodified() };
}
