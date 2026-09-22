// #/impostazioni page (WORKBENCH_SPEC §26.8): the office defaults §23/§24 propose. Full-width,
// no Dati/Sintesi split (js/main.js `showImpostazioni`).
import { el, clear } from "./dom.js";
import { fetchTools } from "./api.js";
import { leggiImpostazioni, salvaImpostazioni, leggiTipi, leggiStoria } from "./impostazioni-api.js";
import { FACTORY, cloneState, isDirty, campiPerStrumento, diffLeggibile } from "./impostazioni-modello.js";
import { buildTipiTable, buildEccezioniSection } from "./impostazioni-passi.js";
import { parseDecimal, formatForInput } from "./number-input.js";
import { trapFocus } from "./nav-state.js";

function formatData(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("it-IT");
  } catch (error) {
    return iso;
  }
}

export function renderImpostazioni(root) {
  clear(root);
  root.append(el("p", { text: "Caricamento…" }));

  Promise.all([leggiImpostazioni(), leggiTipi(), fetchTools()])
    .then(([impostazioniBody, tipiBody, tools]) => renderLoaded(root, impostazioniBody, tipiBody, tools))
    .catch(() => {
      clear(root);
      root.append(el("p", { text: "Impossibile caricare le impostazioni." }));
    });
}

function renderLoaded(root, initialBody, tipiBody, tools) {
  let loadedState = cloneState(initialBody.impostazioni);
  let state = cloneState(initialBody.impostazioni);
  const mappaCampi = campiPerStrumento(tipiBody);
  let revisione = initialBody.revisione;
  let sigla = "";
  // Never mutate `initialBody` in place (rule 12): a save/409-reload replaces these instead of
  // writing back into the object GET returned.
  let aggiornatoIl = initialBody.aggiornato_il;
  let siglaRevisione = initialBody.sigla;

  clear(root);
  root.append(el("h2", { tabindex: "-1", text: "Impostazioni" }));
  root.append(
    el("p", { text: "Valori d'ufficio proposti dal programma. Ogni finestra li mostra e si possono cambiare caso per caso." }),
  );
  const revisioneLine = el("p", { class: "im-revisione" });
  root.append(revisioneLine);

  const avvisiHost = el("div", { class: "im-avvisi" });
  root.append(avvisiHost);

  const liveRegion = el("div", { class: "sr-only", role: "status", "aria-live": "polite" });
  root.append(liveRegion);

  // `tabindex="-1"`: `.focus()` below is a no-op on a plain, non-interactive `<div>` without it.
  const summaryHost = el("div", { class: "im-summary", role: "alert", tabindex: "-1", hidden: true });
  root.append(summaryHost);

  const dirtyChip = el("p", { class: "im-dirty", hidden: true, text: "○ Modifiche non salvate" });
  root.append(dirtyChip);

  const sectionsHost = el("div", { class: "im-sections" });
  root.append(sectionsHost);

  const siglaInput = el("input", { type: "text", id: "im-sigla", maxlength: "12", required: true });
  const salvaBtn = el("button", { type: "button", class: "im-btn-primary", text: "Salva" });
  const annullaBtn = el("button", { type: "button", class: "im-btn", text: "Annulla modifiche" });
  const ripristinaBtn = el("button", { type: "button", class: "im-btn", text: "Ripristina predefiniti" });
  const footer = el("div", { class: "im-footer" }, [
    el("label", { for: "im-sigla", text: "Sigla" }),
    siglaInput,
    salvaBtn,
    annullaBtn,
    ripristinaBtn,
  ]);
  root.append(footer);

  const storiaHost = el("div", { class: "im-storia" });
  root.append(storiaHost);

  function updateRevisioneLine() {
    revisioneLine.textContent = revisione > 0
      ? `Revisione ${revisione} · modificata il ${formatData(aggiornatoIl)} da ${siglaRevisione}`
      : "Valori di fabbrica, mai modificati";
  }
  updateRevisioneLine();

  function renderAvvisi(avvisi) {
    clear(avvisiHost);
    for (const testo of avvisi || []) avvisiHost.append(el("p", { class: "im-avviso", text: `⚠ Attenzione: ${testo}` }));
  }
  renderAvvisi(initialBody.avvisi);

  function updateDirty() {
    dirtyChip.hidden = !isDirty(loadedState, state);
  }

  // `rerender = false` for a plain text-field keystroke ("input" events): `renderSections()`
  // below does `clear(sectionsHost)` and rebuilds every control from scratch, which destroyed
  // the field being typed into (and its focus/caret) after the FIRST character. Only a change
  // that can alter which controls exist at all (a select's own "change", add/remove eccezione,
  // Annulla/Ripristina, a fresh load) still needs the full rebuild.
  function setState(patch, { rerender = true } = {}) {
    state = { ...state, ...patch };
    updateDirty();
    if (rerender) renderSections();
  }

  function renderSections() {
    clear(sectionsHost);

    const obiettivoInput = el("input", { type: "text", id: "im-obiettivo", inputmode: "decimal", value: formatForInput(state.obiettivo_sfruttamento) });
    obiettivoInput.addEventListener("input", () => setState({ obiettivo_sfruttamento: parseDecimal(obiettivoInput.value) }, { rerender: false }));
    const minimoCheckbox = el("input", { type: "checkbox", id: "im-minimo", checked: state.obiettivo_su_verifiche_minimo });
    minimoCheckbox.addEventListener("change", () => setState({ obiettivo_su_verifiche_minimo: minimoCheckbox.checked }));

    sectionsHost.append(
      el("section", { class: "im-section" }, [
        el("h3", { text: "Dimensiona e sensibilità" }),
        el("div", { class: "im-row" }, [el("label", { for: "im-obiettivo", text: "Obiettivo di sfruttamento" }), obiettivoInput, el("span", { class: "im-hint", text: "fabbrica 1,00" })]),
        el("div", { class: "im-row" }, [
          minimoCheckbox,
          el("label", { for: "im-minimo", text: "Applica l'obiettivo anche alle verifiche di minimo e di dettaglio" }),
        ]),
        el("p", { class: "im-hint", text: "Decisione ancora aperta (19-bis): valore di fabbrica no." }),
      ]),
    );

    sectionsHost.append(
      // A passo cell is a plain text field ("input" events, one per keystroke) -- its value
      // changing never alters which controls exist, so never rerender for it either.
      buildTipiTable(tipiBody, state, (tipo, passo) => setState({ passi_per_tipo: { ...state.passi_per_tipo, [tipo]: passo } }, { rerender: false })),
    );

    sectionsHost.append(
      buildEccezioniSection(state, {
        campiPerStrumento: mappaCampi,
        tools,
        // `strutturaChanged`: true for the strumento/campo <select> "change" (the campo options
        // and the cross-row duplicate check both depend on it) -- passo's own "input" never
        // needs it, same reasoning as the tipi table above.
        onChange: (index, patch, strutturaChanged = false) => {
          const next = state.passi_per_campo.map((e, i) => (i === index ? { ...e, ...patch } : e));
          setState({ passi_per_campo: next }, { rerender: strutturaChanged });
        },
        onRemove: (index) => setState({ passi_per_campo: state.passi_per_campo.filter((_, i) => i !== index) }),
        onAdd: () => {
          setState({ passi_per_campo: [...state.passi_per_campo, { strumento: "", campo: "", passo: null }] });
          // §26.8: focus lands on the NEW row's own strumento select, not lost to the button
          // that "Aggiungi" itself was (the rebuild above just replaced it).
          const selects = sectionsHost.querySelectorAll(".im-eccezione-row select");
          const last = selects[selects.length - 2]; // the new row's FIRST select (strumento)
          if (last) last.focus();
        },
      }),
    );
  }
  renderSections();

  siglaInput.addEventListener("input", () => {
    sigla = siglaInput.value;
  });
  siglaInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      onSalva();
    }
  });

  function showSummary(messaggi) {
    clear(summaryHost);
    if (!messaggi || messaggi.length === 0) {
      summaryHost.hidden = true;
      return;
    }
    summaryHost.hidden = false;
    summaryHost.append(el("p", { text: "Correggere prima di salvare:" }));
    const ul = el("ul");
    for (const m of messaggi) ul.append(el("li", { text: m }));
    summaryHost.append(ul);
    summaryHost.focus();
  }

  function onSalva() {
    if (!sigla || sigla.length < 1 || sigla.length > 12) {
      showSummary(["Indicare una sigla di 1-12 caratteri."]);
      return;
    }
    salvaImpostazioni({ impostazioni: state, revisione, sigla }).then((result) => {
      if (result.status === 200) {
        loadedState = cloneState(result.body.impostazioni);
        state = cloneState(result.body.impostazioni);
        revisione = result.body.revisione;
        aggiornatoIl = result.body.aggiornato_il;
        siglaRevisione = result.body.sigla;
        updateRevisioneLine();
        renderAvvisi(result.body.avvisi);
        showSummary(null);
        updateDirty();
        renderSections();
        liveRegion.textContent = `Impostazioni salvate: revisione ${revisione}`;
        aggiornaStoria(); // §26.8: the new revision belongs in "Storia delle modifiche" too
        return;
      }
      if (result.status === 409) {
        showConflictDialog(result.body.attuale);
        return;
      }
      const messaggi = (result.body.errors && result.body.errors.length ? result.body.errors : ["Errore imprevisto."]);
      showSummary(messaggi);
    });
  }
  salvaBtn.onclick = onSalva;

  annullaBtn.onclick = () => {
    state = cloneState(loadedState);
    updateDirty();
    renderSections();
  };

  ripristinaBtn.onclick = () => showConfirmDialog(
    "Ripristinare i valori di fabbrica? Obiettivo 1,00, obiettivo sulle verifiche di minimo no, nessun passo, nessuna eccezione. Diventano effettivi solo con Salva.",
    () => {
      state = cloneState(FACTORY);
      updateDirty();
      renderSections();
    },
  );

  function showConfirmDialog(message, onYes, yesLabel = "Ripristina") {
    const dialog = el("div", { class: "im-dialog", role: "alertdialog", "aria-modal": "true" }, [
      el("p", { text: message }),
      el("div", { class: "im-dialog-actions" }),
    ]);
    const actions = dialog.querySelector(".im-dialog-actions");
    const yes = el("button", { type: "button", class: "im-btn-primary", text: yesLabel });
    const no = el("button", { type: "button", class: "im-btn", text: "Annulla" });
    actions.append(yes, no);
    const overlay = el("div", { class: "im-overlay" }, [dialog]);
    root.append(overlay);
    const release = trapFocus(dialog, { onEscape: close });
    function close() {
      overlay.remove();
      release();
    }
    yes.onclick = () => {
      close();
      onYes();
    };
    no.onclick = close;
    no.focus();
  }

  function showConflictDialog(attuale) {
    const dialog = el("div", { class: "im-dialog", role: "alertdialog", "aria-modal": "true" }, [
      el("p", { text: `Le impostazioni sono state modificate nel frattempo (revisione ${attuale.revisione}, sigla ${attuale.sigla}): ricaricare e riprovare.` }),
      el("div", { class: "im-dialog-actions" }),
    ]);
    const actions = dialog.querySelector(".im-dialog-actions");
    const ricarica = el("button", { type: "button", class: "im-btn-primary", text: "Ricarica" });
    const chiudi = el("button", { type: "button", class: "im-btn", text: "Chiudi" });
    actions.append(ricarica, chiudi);
    const overlay = el("div", { class: "im-overlay" }, [dialog]);
    root.append(overlay);
    const release = trapFocus(dialog, { onEscape: close });
    function close() {
      overlay.remove();
      release();
    }
    function applyRicarica() {
      loadedState = cloneState(attuale.impostazioni);
      state = cloneState(attuale.impostazioni);
      revisione = attuale.revisione;
      aggiornatoIl = attuale.aggiornato_il;
      siglaRevisione = attuale.sigla;
      updateRevisioneLine();
      updateDirty();
      renderSections();
    }
    ricarica.onclick = () => {
      close();
      // §26.8: a second confirmation before discarding the LOCAL edits that just failed to save
      // (they were dirty enough to attempt a save at all) -- "Ricarica" here means "someone else's
      // revision wins", never a silent no-op the engineer might mistake for "my Salva went through".
      if (isDirty(loadedState, state)) {
        showConfirmDialog("Ricaricare scarta le modifiche locali non salvate. Continuare?", applyRicarica, "Ricarica");
      } else {
        applyRicarica();
      }
    };
    chiudi.onclick = close;
    ricarica.focus();
  }

  function renderStoria(righe) {
    clear(storiaHost);
    const details = el("details", { class: "im-storia-details" });
    details.append(el("summary", { text: "Storia delle modifiche" }));
    const table = el("table", {}, [
      el("caption", { text: "Storia delle impostazioni" }),
      el("thead", {}, [el("tr", {}, ["Revisione", "Data", "Sigla", "Che cosa è cambiato"].map((t) => el("th", { text: t })))]),
    ]);
    const tbody = el("tbody");
    for (let i = 0; i < righe.length; i += 1) {
      const voce = righe[i];
      const precedente = righe[i + 1];
      const cambi = precedente ? diffLeggibile(precedente.valori, voce.valori).join("; ") : "Prima revisione salvata";
      tbody.append(
        el("tr", {}, [
          el("td", { text: String(voce.revisione) }),
          el("td", { text: formatData(voce.aggiornato_il) }),
          el("td", { text: voce.sigla }),
          el("td", { text: cambi || "—" }),
        ]),
      );
    }
    table.append(tbody);
    details.append(table);
    storiaHost.append(details);
  }
  function aggiornaStoria() {
    leggiStoria().then(renderStoria).catch(() => {});
  }
  aggiornaStoria();

  // Module-level "current dirty check" (same "last mount wins" pattern as js/annulla-ui.js's own
  // `activeTool`) -- the actual `beforeunload` listener is registered ONCE at module load
  // (further down), never once per visit to this page: adding a new one here every time without
  // ever removing the old kept every past visit's closure alive AND asking the browser to confirm
  // once per accumulated listener.
  currentIsDirty = () => isDirty(loadedState, state);
}

let currentIsDirty = () => false;
window.addEventListener("beforeunload", (event) => {
  if (!currentIsDirty()) return;
  event.preventDefault();
  event.returnValue = "";
});
