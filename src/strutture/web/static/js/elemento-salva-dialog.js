// The "Salva in progetto"/"Salva come nuovo"/"Salva come copia" create-element dialog, extracted
// out of js/elemento-salva.js (WORKBENCH_SPEC §25.4: "if a further need arises that would push it
// over 400 lines, the 409-conflict dialog is split out first" -- that dialog already lives in
// js/elemento-conflitto.js; this create dialog is the next piece big enough to move on its own,
// same "no cycle, caller keeps all its own state" shape as that split).
import { el, clear } from "./dom.js";
import { trapFocus } from "./nav-state.js";
import { getCurrentProgetto, setCurrentProgetto } from "./progetto-picker.js";
import { whenSettled } from "./live.js";
import { fetchProgetti, fetchProgetto, createProgetto, fetchElementi, createElemento } from "./progetti-api.js";

const NEW_PROJECT_VALUE = "__nuovo__";

async function defaultElementName(progettoId, title, tool) {
  const base = title || tool;
  if (!progettoId) return `${base} 1`;
  try {
    const elementi = await fetchElementi(progettoId);
    return `${base} ${elementi.filter((item) => item.strumento === tool).length + 1}`;
  } catch (error) {
    return `${base} 1`;
  }
}

// One dialog for "Salva in progetto", "Salva come nuovo" and "Salva come copia": all three create
// a NEW element, only the pre-filled name/project differ. The project picker sits INSIDE this
// dialog rather than a separate wizard step, so "with no project selected it opens the picker
// first" (§14.1) is just this same dialog with nothing preselected.
//
// `caller` bundles everything the dialog needs from js/elemento-salva.js's own closure:
// `{ tool, title, loaded, currentPayload, closeDialog, onCreated }` -- `onCreated(created,
// targetId, targetNome, sigla, nota)` is called on success so the caller updates its own `loaded`/
// footprint/widget state (this module never touches them directly).
export async function openCreateDialog(caller, { progettoId, defaultNome } = {}) {
  const { tool, title, loaded, currentPayload, closeDialog, onCreated } = caller;
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
  nomeInput.value = defaultNome || (await defaultElementName(startProgettoId, title, tool));

  progettoSelect.addEventListener("change", async () => {
    newProjectHost.hidden = progettoSelect.value !== NEW_PROJECT_VALUE;
    if (!newProjectHost.hidden) {
      newNomeInput.focus();
      return;
    }
    if (nomeTouched || defaultNome) return;
    const computed = await defaultElementName(progettoSelect.value, title, tool);
    // Re-checked AFTER the await: typing a custom name while this fetch was still in flight must
    // never have it clobbered the instant the fetch resolves.
    if (nomeTouched || defaultNome) return;
    nomeInput.value = computed;
  });

  // Same "no role=alert" reasoning as the widget's own `errorEl`: this dialog is opened from a
  // tool page, so it too would be additive to that page's already-fixed 3 live regions.
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

  const dialogEl = el("dialog", { class: "es-dialog", role: "dialog", "aria-modal": "true", "aria-labelledby": titleId }, [
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
      onCreated(created, targetId, targetNome, siglaInput.value.trim(), notaInput.value.trim());
      closeDialog();
    } catch (error) {
      showDialogError(error.message || "Impossibile salvare l'elemento.");
    } finally {
      saveButton.disabled = false;
    }
  });

  const releaseTrap = trapFocus(dialogEl, { onEscape: closeDialog });
  dialogEl.showModal();
  (progettoSelect.value ? nomeInput : progettoSelect).focus();
  return { dialogEl, releaseTrap };
}
