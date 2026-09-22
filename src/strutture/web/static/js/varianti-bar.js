// "Varianti affiancate" (WORKBENCH_SPEC §19.2): "Crea variante" in the Dati action bar + the
// variant strip (`role="tablist"`) above the form. Mounted by js/forms.js's `renderForm`, same
// lazy-`getApi` pattern as js/elemento-salva.js/js/annulla-ui.js. Persistence/pure transitions
// live in js/varianti-state.js; this module owns the DOM only.
import { el, clear } from "./dom.js";
import { save } from "./form-state.js";
import { requestRun } from "./live.js";
import { navigate } from "./router.js";
import { azzeraStoriaAnnulla } from "./annulla-ui.js";
import {
  MAX_VARIANTI,
  caricaVarianti,
  salvaVarianti,
  chiudiVarianti,
  iniziaVarianti,
  aggiungiVariante,
  duplicaVariante,
  attivaVariante,
  rinominaVariante,
  eliminaVariante,
  aggiornaInputsVariante,
  puoAggiungere,
  varianteAttiva,
  etichettaTab,
} from "./varianti-state.js";

// Mounted by js/forms.js's `renderForm`, once per tool page. `origine` (§19.2: "when the form was
// opened from an element, A carries origine") is `{elemento_id, revisione, nome} | null`, read
// from js/provenienza.js's own state the same way js/elemento-salva.js already does.
export function mountVariantiBar({ tool, fields, getApi, getOrigine }) {
  let set = caricaVarianti(tool);
  let applyingSet = false; // suppresses re-recording our OWN api.setValues() as a form edit

  // Two SEPARATE elements, not one widget: §19.2 puts "Crea variante" in the Dati action bar
  // (next to "Carica esempio") but the strip itself ABOVE the form, under the §15/§16 notices --
  // js/forms.js places each in its own slot.
  const creaBtn = el("button", { type: "button", class: "vb-crea", text: "⧉ Crea variante" });
  const strip = el("div", { class: "vb-strip", role: "tablist", "aria-label": "Varianti" });

  function persist() {
    salvaVarianti(tool, set);
  }

  function applyActive() {
    const api = getApi();
    const attiva = varianteAttiva(set);
    if (!api || !attiva) return;
    applyingSet = true;
    api.setValues(attiva.inputs);
    applyingSet = false;
    const values = api.values();
    save(tool, values, fields);
    requestRun(tool, values, "manual");
  }

  function buildTabMenu(variante) {
    const menu = el("details", { class: "vb-menu" });
    menu.append(el("summary", { class: "vb-menu-btn", "aria-label": `Altre azioni per la variante ${variante.id}` }, [document.createTextNode("⋯")]));
    const renameInput = el("input", { type: "text", class: "vb-rename-input", value: variante.nome, maxlength: "40", "aria-label": `Rinomina variante ${variante.id}` });
    const renameBtn = el("button", { type: "button", class: "vb-menu-item", text: "Rinomina", onclick: () => {
      set = rinominaVariante(set, variante.id, renameInput.value);
      persist();
      render();
    } });
    const duplicaBtn = el("button", { type: "button", class: "vb-menu-item", text: "Duplica", disabled: !puoAggiungere(set), onclick: () => {
      set = duplicaVariante(set, variante.id);
      persist();
      render();
      applyActive();
    } });
    const items = [el("div", { class: "vb-menu-rename" }, [renameInput, renameBtn]), duplicaBtn];
    if (set.varianti.length > 1) {
      items.push(
        el("button", { type: "button", class: "vb-menu-item vb-menu-item--danger", text: "Elimina", onclick: () => {
          const eraAttiva = set.attiva === variante.id;
          set = eliminaVariante(set, variante.id);
          persist();
          render();
          if (eraAttiva) applyActive();
        } }),
      );
    }
    menu.append(...items);
    return menu;
  }

  function buildTab(variante) {
    const attivo = variante.id === set.attiva;
    const tab = el("button", {
      type: "button",
      role: "tab",
      class: "vb-tab",
      "aria-selected": String(attivo),
      tabindex: attivo ? "0" : "-1",
      text: etichettaTab(variante),
      onclick: () => activate(variante.id),
    });
    return el("div", { class: "vb-tab-wrap" }, [tab, buildTabMenu(variante)]);
  }

  function activate(id) {
    if (id === set.attiva) return;
    set = attivaVariante(set, id);
    persist();
    render();
    applyActive();
  }

  function moveFocus(delta) {
    const tabs = [...strip.querySelectorAll('[role="tab"]')];
    const index = tabs.indexOf(document.activeElement);
    if (index === -1) return;
    const nextIndex = (index + delta + tabs.length) % tabs.length;
    const nextId = set.varianti[nextIndex].id;
    activate(nextId);
    // `render()` inside `activate()` rebuilt every tab node: re-find the new one by id (its
    // position in `set.varianti` is unchanged) rather than reuse the now-detached `tabs[nextIndex]`.
    const rebuilt = [...strip.querySelectorAll('[role="tab"]')][nextIndex];
    if (rebuilt) rebuilt.focus();
  }

  function renderConfirmChiudi() {
    clear(strip);
    strip.append(
      el("span", { class: "vb-confirm-text", text: "Le varianti non salvate saranno scartate." }),
      el("button", { type: "button", class: "vb-confirm-yes", text: "Chiudi e scarta", onclick: () => {
        chiudiVarianti(tool);
        set = null;
        render();
      } }),
      el("button", { type: "button", class: "vb-confirm-no", text: "Annulla", onclick: render }),
    );
  }

  function render() {
    clear(strip);
    creaBtn.disabled = Boolean(set) && !puoAggiungere(set);
    creaBtn.title = creaBtn.disabled ? "Massimo 4 varianti" : "";
    if (!set) {
      strip.hidden = true;
      return;
    }
    strip.hidden = false;
    for (const variante of set.varianti) strip.append(buildTab(variante));
    strip.append(
      el("button", { type: "button", class: "vb-affianca", text: "Affianca", onclick: () => navigate(`varianti/${tool}`) }),
      el("button", { type: "button", class: "vb-chiudi", text: "Chiudi varianti", onclick: renderConfirmChiudi }),
    );
  }

  creaBtn.addEventListener("click", () => {
    const api = getApi();
    if (!api) return;
    if (!set) {
      set = iniziaVarianti(api.allValues(), getOrigine ? getOrigine() : null);
    } else if (puoAggiungere(set)) {
      set = aggiungiVariante(set);
    } else {
      return;
    }
    persist();
    // A brand-new variant set is a history boundary the same way §21.1 treats "Carica esempio":
    // the newly-active variant's inputs are not an edit of what was on screen a moment ago.
    azzeraStoriaAnnulla();
    render();
    applyActive();
  });

  strip.addEventListener("keydown", (event) => {
    if (event.target.getAttribute("role") !== "tab") return;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      moveFocus(-1);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      moveFocus(1);
    }
  });

  // Every valid form edit (§19.2 "Every valid form change updates the active variant's inputs"),
  // called by js/forms.js's own `handleChange` right after its normal `save()`.
  function onValidChange(values) {
    if (applyingSet || !set) return;
    const attiva = varianteAttiva(set);
    if (!attiva) return;
    set = aggiornaInputsVariante(set, attiva.id, values);
    persist();
    render();
  }

  render();
  // §19.2 "coming back restores the strip and the active variant": `getApi()` only resolves once
  // js/forms.js's `renderForm` finishes assigning it (same temporal-dead-zone reason as every
  // other lazy-`getApi` widget here) -- a microtask is enough since nothing else touches the form
  // synchronously after this module returns.
  if (set) Promise.resolve().then(applyActive);

  return { creaButton: creaBtn, stripElement: strip, onValidChange };
}
