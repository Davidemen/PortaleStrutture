// "Salva in progetto" (WORKBENCH_SPEC §14.1): the Dati action-bar widget (button + header-state
// text), its create/"Salva come nuovo" dialog, the 409 conflict dialog and the `?elemento=<id>`
// deep-link loader. Mounted directly by js/forms.js's `renderForm` (a plain function call, not an
// event listener -- `#form-actions` is rebuilt synchronously on every `strutture:tool-schema`, and
// mounting via a document-level listener of our own could race forms.js's OWN listener that clears
// the bar first) so ordering is guaranteed rather than left to dynamic-import timing.
import { el, clear } from "./dom.js";
import { trapFocus } from "./nav-state.js";
import { visibleValues } from "./forms-sections.js";
import { save } from "./form-state.js";
import { requestRun, whenSettled } from "./live.js";
import { getCurrentProgetto, setCurrentProgetto } from "./progetto-picker.js";
import { takeAnteprimaStash } from "./progetto-anteprima.js";
import { computeSintesiEStato } from "./elemento-sintesi.js";
import { activeProvenienza, reconstructProvenienza } from "./provenienza.js";
import { azzeraStoriaAnnulla } from "./annulla-ui.js";
import { apriConflittoDialog } from "./elemento-conflitto.js";
import {
  fetchProgetti,
  fetchProgetto,
  createProgetto,
  fetchElementi,
  createElemento,
  fetchElemento,
  updateElemento,
} from "./progetti-api.js";

const NEW_PROJECT_VALUE = "__nuovo__";

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
      renderWidgetState();
      showStatus("Elemento salvato.");
    } catch (error) {
      showError(error.message);
    } finally {
      saveBtn.disabled = false;
    }
  }

  async function defaultElementName(progettoId) {
    const base = title || tool;
    if (!progettoId) return `${base} 1`;
    try {
      const elementi = await fetchElementi(progettoId);
      return `${base} ${elementi.filter((item) => item.strumento === tool).length + 1}`;
    } catch (error) {
      return `${base} 1`;
    }
  }

  // One dialog for "Salva in progetto", "Salva come nuovo" and "Salva come copia": all three
  // create a NEW element, only the pre-filled name/project differ. The project picker sits INSIDE
  // this dialog rather than a separate wizard step, so "with no project selected it opens the
  // picker first" (§14.1) is just this same dialog with nothing preselected.
  async function openCreateDialog({ progettoId, defaultNome } = {}) {
    closeDialog();
    const current = getCurrentProgetto();
    const startProgettoId = progettoId || (current && current.id) || "";
    let progetti = [];
    try {
      progetti = await fetchProgetti();
    } catch (error) {
      // the dialog still offers "Nuovo progetto..." even when the list failed to load
    }

    const titleId = "es-dialog-title";
    const progettoSelect = el("select", { id: "es-dialog-progetto", required: true });
    const newProjectHost = el("div", { class: "es-new-progetto" });
    newProjectHost.hidden = true;
    const newNomeInput = el("input", { type: "text", id: "es-new-progetto-nome", maxlength: "120" });
    const newCodiceInput = el("input", { type: "text", id: "es-new-progetto-codice", maxlength: "40" });
    const newCommittenteInput = el("input", { type: "text", id: "es-new-progetto-committente", maxlength: "120" });
    newProjectHost.append(
      el("div", { class: "es-dialog-field" }, [el("label", { for: "es-new-progetto-nome", text: "Nome del nuovo progetto" }), newNomeInput]),
      el("div", { class: "es-dialog-field" }, [el("label", { for: "es-new-progetto-codice", text: "Codice" }), newCodiceInput]),
      el("div", { class: "es-dialog-field" }, [el("label", { for: "es-new-progetto-committente", text: "Committente" }), newCommittenteInput]),
    );

    function renderProgettoOptions(selectedId) {
      clear(progettoSelect);
      progettoSelect.append(el("option", { value: "", text: "Seleziona un progetto…" }));
      for (const progetto of progetti) {
        const text = progetto.codice ? `${progetto.codice} — ${progetto.nome}` : progetto.nome;
        progettoSelect.append(el("option", { value: progetto.id, text, selected: progetto.id === selectedId }));
      }
      progettoSelect.append(el("option", { value: NEW_PROJECT_VALUE, text: "Nuovo progetto…" }));
    }
    renderProgettoOptions(startProgettoId);

    const nomeInput = el("input", { type: "text", id: "es-dialog-nome", required: true, maxlength: "120" });
    const siglaInput = el("input", { type: "text", id: "es-dialog-sigla", maxlength: "8" });
    const notaInput = el("textarea", { id: "es-dialog-nota", rows: "2", maxlength: "2000" });
    let nomeTouched = false;
    nomeInput.addEventListener("input", () => {
      nomeTouched = true;
    });
    nomeInput.value = defaultNome || (await defaultElementName(startProgettoId));

    progettoSelect.addEventListener("change", async () => {
      newProjectHost.hidden = progettoSelect.value !== NEW_PROJECT_VALUE;
      if (!newProjectHost.hidden) {
        newNomeInput.focus();
        return;
      }
      if (nomeTouched || defaultNome) return;
      const computed = await defaultElementName(progettoSelect.value);
      // Re-checked AFTER the await: typing a custom name while this fetch was still in flight
      // must never have it clobbered the instant the fetch resolves.
      if (nomeTouched || defaultNome) return;
      nomeInput.value = computed;
    });

    // Same "no role=alert" reasoning as the widget's own `errorEl` above: this dialog is opened
    // from a tool page, so it too would be additive to that page's already-fixed 3 live regions.
    const dialogErrorEl = el("p", { class: "es-dialog-error" });
    dialogErrorEl.hidden = true;
    const saveButton = el("button", { type: "submit", class: "es-dialog-save", text: "Salva" });
    const form = el("form", { class: "es-dialog-form" }, [
      el("div", { class: "es-dialog-field" }, [el("label", { for: "es-dialog-progetto", text: "Progetto" }), progettoSelect]),
      newProjectHost,
      el("div", { class: "es-dialog-field" }, [el("label", { for: "es-dialog-nome", text: "Nome elemento" }), nomeInput]),
      el("div", { class: "es-dialog-field" }, [el("label", { for: "es-dialog-sigla", text: "Sigla" }), siglaInput]),
      el("div", { class: "es-dialog-field" }, [el("label", { for: "es-dialog-nota", text: "Nota" }), notaInput]),
      dialogErrorEl,
      el("div", { class: "es-dialog-actions" }, [saveButton, el("button", { type: "button", class: "es-dialog-cancel", text: "Annulla", onclick: closeDialog })]),
    ]);

    dialogEl = el("dialog", { class: "es-dialog", role: "dialog", "aria-modal": "true", "aria-labelledby": titleId }, [
      el("h2", { id: titleId, text: loaded ? "Salva come nuovo" : "Salva in progetto" }),
      form,
    ]);
    document.body.append(dialogEl);
    dialogEl.addEventListener("close", closeDialog);

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      dialogErrorEl.hidden = true;
      let targetId = progettoSelect.value;
      let targetNome = null;
      if (targetId === NEW_PROJECT_VALUE) {
        const nome = newNomeInput.value.trim();
        if (!nome) return showDialogError("Il nome del nuovo progetto è obbligatorio.");
        try {
          const created = await createProgetto({ codice: newCodiceInput.value.trim(), nome, committente: newCommittenteInput.value.trim() });
          targetId = created.id;
          targetNome = created.nome;
          setCurrentProgetto(created);
        } catch (error) {
          return showDialogError(error.message || "Impossibile creare il progetto.");
        }
      }
      if (!targetId) return showDialogError("Scegli un progetto.");
      const nome = nomeInput.value.trim();
      if (!nome) return showDialogError("Il nome dell'elemento è obbligatorio.");

      function showDialogError(message) {
        dialogErrorEl.textContent = message;
        dialogErrorEl.hidden = false;
      }

      saveButton.disabled = true;
      try {
        await whenSettled(); // §20.1: the saved sintesi belongs to the saved inputs
        const created = await createElemento(targetId, currentPayload(nome, siglaInput.value.trim(), notaInput.value.trim()));
        if (!targetNome) {
          const found = progetti.find((progetto) => progetto.id === targetId);
          targetNome = found ? found.nome : await fetchProgetto(targetId).then((p) => p.nome).catch(() => "");
        }
        loaded = {
          id: created.id,
          revisione: created.revisione,
          nome: created.nome,
          sigla: siglaInput.value.trim(),
          nota: notaInput.value.trim(),
          progettoId: targetId,
          progettoNome: targetNome,
        };
        const current2 = getCurrentProgetto();
        if (!current2 || current2.id !== targetId) setCurrentProgetto({ id: targetId, nome: targetNome });
        renderWidgetState();
        closeDialog();
        showStatus("Elemento salvato in progetto.");
      } catch (error) {
        showDialogError(error.message || "Impossibile salvare l'elemento.");
      } finally {
        saveButton.disabled = false;
      }
    });

    releaseTrap = trapFocus(dialogEl, { onEscape: closeDialog });
    dialogEl.showModal();
    (progettoSelect.value ? nomeInput : progettoSelect).focus();
  }

  function applyReload(attuale) {
    const api = getApi();
    if (api) api.setValues(attuale.inputs || {});
    azzeraStoriaAnnulla(); // WORKBENCH_SPEC §21.1: "Ricarica" is a history boundary
    const values = visibleValues(toolForm, fields);
    save(tool, values, fields);
    requestRun(tool, values, "manual");
    loaded = loaded ? { ...loaded, revisione: attuale.revisione, nome: attuale.nome } : loaded;
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
      let progettoNome = "";
      try {
        progettoNome = (await fetchProgetto(elemento.progetto_id)).nome;
      } catch (error) {
        progettoNome = "";
      }
      loaded = { id: elemento.id, revisione: elemento.revisione, nome: elemento.nome, sigla: "", nota: "", progettoId: elemento.progetto_id, progettoNome };
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
  // is eligible. `tool` closes over this mount's own tool name so a stale reference from a
  // previous page can never answer for the wrong tool.
  currentTool = tool;
  currentLoaded = () => loaded;

  return wrap;
}

// Module-level, like js/provenienza.js's own `session`: only one tool page is ever mounted at a
// time, so the LATEST `mountElementoSalva` call always wins.
let currentTool = null;
let currentLoaded = () => null;

export function loadedElementState(tool) {
  if (currentTool !== tool) return null;
  const loaded = currentLoaded();
  return loaded ? { id: loaded.id, revisione: loaded.revisione } : null;
}
