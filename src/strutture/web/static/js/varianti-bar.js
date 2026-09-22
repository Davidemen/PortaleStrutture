// "Varianti affiancate" (WORKBENCH_SPEC §19.2): "Crea variante" in the Dati action bar + the
// variant strip (`role="tablist"`) above the form. Mounted by js/forms.js's `renderForm`, same
// lazy-`getApi` pattern as js/elemento-salva.js/js/annulla-ui.js. Persistence/pure transitions
// live in js/varianti-state.js; this module owns the DOM only.
import { el, clear } from "./dom.js";
import { save } from "./form-state.js";
import { requestRun } from "./live.js";
import { navigate } from "./router.js";
import { azzeraStoriaAnnulla, setHistoryScope } from "./annulla-ui.js";
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
    // §21.1/§19.2: every write of a variant's inputs into the form is scoped to THAT variant's
    // own undo history -- called AFTER `api.setValues()` above (never before), so the snapshot
    // this scope's history baselines against is the value now actually ON SCREEN, not whatever
    // the PREVIOUS variant still held the instant before `setValues()` ran (`setValues()` never
    // dispatches a native "change", so nothing else would catch that staleness).
    setHistoryScope(`${tool}#${attiva.id}`);
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
        // Back to the tool's own plain (non-variant) undo history -- otherwise a Ctrl+Z right
        // after closing the set would still act on whichever variant was active last.
        setHistoryScope(tool);
        render();
      } }),
      el("button", { type: "button", class: "vb-confirm-no", text: "Annulla", onclick: render }),
    );
  }

  // §19.2: "Variante B di 3" next to the tool title -- the ONLY place in the DOM outside this
  // widget's own strip/Affianca page that names the current variant, so an engineer scrolled past
  // the strip still knows which one is on screen. `#tool-title` is js/main.js's own element (a
  // plain DOM id, not a module import, to avoid a cycle back into main.js); harmless no-op when
  // this page is not a tool page at all (never happens while `mountVariantiBar` is mounted).
  function renderTitleBadge() {
    const titleEl = document.getElementById("tool-title");
    if (!titleEl) return;
    const existing = titleEl.querySelector(".vb-title-badge");
    if (existing) existing.remove();
    if (!set) return;
    titleEl.append(el("span", { class: "vb-title-badge", text: ` — Variante ${set.attiva} di ${set.varianti.length}` }));
  }

  function render() {
    clear(strip);
    creaBtn.disabled = Boolean(set) && !puoAggiungere(set);
    creaBtn.title = creaBtn.disabled ? "Massimo 4 varianti" : "";
    renderTitleBadge();
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
    render();
    // `applyActive()` below scopes the undo history to the newly-active variant's OWN id first
    // (js/annulla-ui.js's `setHistoryScope`) -- a brand-new scope already starts empty, but
    // `azzeraStoriaAnnulla()` after it still enforces the boundary explicitly (§21.1, same as
    // "Carica esempio") for the rare case this scope was already visited earlier in the tab's
    // life (e.g. re-adding a variant after deleting it) and would otherwise resume old steps.
    applyActive();
    azzeraStoriaAnnulla();
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
