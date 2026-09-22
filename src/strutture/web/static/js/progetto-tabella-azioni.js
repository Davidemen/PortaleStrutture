// The per-row "⋯ Azioni" menu of js/progetto-tabella.js (Duplica/Rinomina/Storia/Elimina, plus the
// §25.4 "Aggiorna dai dati a monte"/"Apri l'origine <sigla>" actions) -- extracted purely to keep
// that module under the 400-line cap. Takes every piece of caller state it needs (`elementi`,
// `onChange`) rather than importing progetto-tabella.js back, so there is no cycle.
import { el, clear } from "./dom.js";
import { navigate } from "./router.js";
import { duplicateElemento, updateElemento, deleteElemento } from "./progetti-api.js";
import { buildProgettoStoria } from "./progetto-storia.js";

// §25.4: "Aggiorna dai dati a monte" only when da_ricalcolare comes from the element's OWN
// values (`motivi` with a `chiave`, i.e. not purely `origine_da_ricalcolare`/`ciclo_origini`/
// `controllo_rinviato`) -- same filter as js/progetto-stato.js's own `motiviRicalcolo`.
function motiviPropri(voce) {
  return (voce.motivi || []).filter((m) => m.causa !== "origine_da_ricalcolare" && m.causa !== "ciclo_origini" && m.causa !== "controllo_rinviato");
}

// §25.1/§25.4: "Apri l'origine <sigla>" when da_ricalcolare is caused ONLY by a propagated
// provider (no own motivo at all) -- opens the FARTHEST-named direct provider from `motivi`.
function motivoOrigine(voce) {
  return (voce.motivi || []).find((m) => m.causa === "origine_da_ricalcolare" && m.elemento_id);
}

function siglaOf(toolsByName, strumento) {
  const tool = toolsByName && toolsByName.get(strumento);
  return tool ? tool.sigla : strumento;
}

export function buildAzioniMenu({ elemento, cell, elementi, onChange, statoVoce, aggiornaOriginiUrl, toolsByName }) {
  function replaceElemento(next) {
    onChange(elementi.map((item) => (item.id === next.id ? next : item)));
  }
  function markDeleted(id) {
    const now = new Date().toISOString();
    onChange(elementi.map((item) => (item.id === id ? { ...item, eliminato: now, aggiornato: now, revisione: item.revisione + 1 } : item)));
  }

  const errorEl = el("p", { class: "pt-row-error", role: "alert", hidden: true });
  function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = false;
  }
  function inlineForm(defaultValue, label, onSubmit) {
    clear(cell);
    const input = el("input", { type: "text", class: "pt-inline-input", value: defaultValue, maxlength: "120", required: true });
    const saveBtn = el("button", { type: "button", class: "pt-action", text: label, onclick: () => onSubmit(input.value.trim(), saveBtn) });
    const cancelBtn = el("button", { type: "button", class: "pt-action", text: "Annulla", onclick: () => renderMenu() });
    cell.append(input, saveBtn, cancelBtn, errorEl);
    input.focus();
    input.select();
  }
  function renameForm() {
    inlineForm(elemento.nome, "Salva", async (nome, btn) => {
      if (!nome) return showError("Il nome è obbligatorio.");
      btn.disabled = true;
      try {
        const result = await updateElemento(elemento.id, {
          strumento: elemento.strumento, nome, inputs: elemento.inputs, sintesi: elemento.sintesi,
          stato: elemento.stato, modalita: elemento.modalita, provenienza: elemento.provenienza, revisione: elemento.revisione,
          sigla: elemento.sigla, nota: elemento.nota,
        });
        if (result.conflict) return showError(result.message || "Modificato da un altro utente: ricarica e riprova.");
        replaceElemento(result.data);
      } catch (error) {
        showError(error.message || "Impossibile rinominare.");
        btn.disabled = false;
      }
    });
  }
  function duplicaForm() {
    inlineForm(`${elemento.nome} (copia)`, "Duplica", async (nome, btn) => {
      if (!nome) return showError("Il nome è obbligatorio.");
      btn.disabled = true;
      try {
        const created = await duplicateElemento(elemento.id, nome);
        onChange([created, ...elementi]);
      } catch (error) {
        showError(error.message || "Impossibile duplicare.");
        btn.disabled = false;
      }
    });
  }
  function deleteConfirm() {
    clear(cell);
    const confirmBtn = el("button", {
      type: "button", class: "pt-action pt-action--danger", text: "Conferma eliminazione",
      onclick: async () => {
        confirmBtn.disabled = true;
        try {
          const result = await deleteElemento(elemento.id, elemento.revisione);
          if (result.conflict) return showError(result.message || "Modificato da un altro utente: ricarica e riprova.");
          markDeleted(elemento.id);
        } catch (error) {
          showError(error.message || "Impossibile eliminare.");
          confirmBtn.disabled = false;
        }
      },
    });
    cell.append(el("span", { text: "Confermi l'eliminazione? " }), confirmBtn, el("button", { type: "button", class: "pt-action", text: "Annulla", onclick: () => renderMenu() }), errorEl);
  }
  function aggiornaOrigini() {
    window.location.hash = aggiornaOriginiUrl;
  }
  function apriOrigine() {
    const motivo = motivoOrigine(statoVoce);
    if (motivo) navigate(motivo.strumento, { elemento: motivo.elemento_id });
  }

  let storiaOpen = false;
  function toggleStoria() {
    storiaOpen = !storiaOpen;
    renderMenu();
  }

  function renderMenu() {
    clear(cell);
    const menuBtn = el("button", { type: "button", class: "pt-azioni-btn", text: "⋯ Azioni", "aria-haspopup": "true" });
    const menu = el("div", { class: "pt-menu", role: "menu", hidden: true });
    const menuItems = () => Array.from(menu.querySelectorAll(".pt-menu-item"));
    function onDocClick(event) {
      if (event.target === menuBtn || menu.contains(event.target)) return;
      closeMenu();
    }
    // `focusButton`: false for an item's own onclick (renameForm/duplicaForm/deleteConfirm/
    // toggleStoria/aggiornaOrigini/apriOrigine each move focus/navigation elsewhere -- clobbering
    // that back onto "⋯ Azioni" a tick later would be a worse regression than the one being fixed).
    function closeMenu(focusButton = true) {
      menu.hidden = true;
      menuBtn.setAttribute("aria-expanded", "false");
      document.removeEventListener("click", onDocClick);
      if (focusButton) menuBtn.focus();
    }
    function openMenu() {
      menu.hidden = false;
      menuBtn.setAttribute("aria-expanded", "true");
      document.addEventListener("click", onDocClick);
      const items = menuItems();
      if (items[0]) items[0].focus();
    }
    const item = (text, onclick) => el("button", { type: "button", class: "pt-menu-item", role: "menuitem", text, onclick: () => { closeMenu(false); onclick(); } });
    const items = [item("Duplica", duplicaForm), item("Rinomina", renameForm)];
    if (statoVoce && statoVoce.da_ricalcolare && motiviPropri(statoVoce).length > 0) {
      items.push(item("Aggiorna dai dati a monte", aggiornaOrigini));
    }
    if (statoVoce && statoVoce.da_ricalcolare && motiviPropri(statoVoce).length === 0 && motivoOrigine(statoVoce)) {
      items.push(item(`Apri l'origine ${siglaOf(toolsByName, motivoOrigine(statoVoce).strumento)}`, apriOrigine));
    }
    items.push(item(storiaOpen ? "Nascondi storia" : "Storia", toggleStoria), item("Elimina", deleteConfirm));
    menu.append(...items);
    menuBtn.addEventListener("click", () => {
      if (menu.hidden) openMenu();
      else closeMenu();
    });
    menu.addEventListener("keydown", (event) => {
      const currentItems = menuItems();
      const index = currentItems.indexOf(document.activeElement);
      if (event.key === "Escape") {
        event.preventDefault();
        closeMenu();
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        if (currentItems[index + 1]) currentItems[index + 1].focus();
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        if (index > 0) currentItems[index - 1].focus();
      }
    });
    cell.append(menuBtn, menu);
    if (storiaOpen) {
      const details = buildProgettoStoria(elemento);
      cell.append(details);
      details.open = true; // opening it FROM the menu should not need a second click
    }
  }
  renderMenu();
}
