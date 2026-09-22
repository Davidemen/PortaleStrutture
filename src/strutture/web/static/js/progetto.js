// #/progetti/<id> (WORKBENCH_SPEC §14.3): head (codice/nome/committente/note, each editable
// inline with PUT + revisione), Esporta (downloads the JSON export), Relazione di progetto, then
// the element list (js/progetto-elementi.js). The shell renders this full-width (js/main.js
// `showProgettoPage`).
import { el, clear } from "./dom.js";
import { fetchProgetto, updateProgetto, fetchExportPayload } from "./progetti-api.js";
import { renderProgettoElementi } from "./progetto-elementi.js";
import { openRelazioneProgetto } from "./progetto-relazione.js";

function notifyProgettiChanged() {
  document.dispatchEvent(new CustomEvent("strutture:progetti-changed"));
}

function safeFileName(text) {
  return (text || "progetto").replace(/[^\w\-]+/g, "_").slice(0, 80);
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = el("a", { href: url, download: filename });
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

const FIELD_DEFS = [
  { key: "codice", label: "Codice", maxlength: 40 },
  { key: "nome", label: "Nome", maxlength: 120, required: true },
  { key: "committente", label: "Committente", maxlength: 120 },
  { key: "note", label: "Note", maxlength: 4000, multiline: true },
];

// `root` here is `js/main.js`'s single `#progetti-pane` node, SHARED with js/progetti.js's own
// `renderProgettiList` (`showProgetti()` routes BOTH `#/progetti` and `#/progetti/<id>` into the
// very same element) -- a navigation from a project page straight to the list (or to a DIFFERENT
// project) can start this async function again, or hand the very same root to the OTHER module
// entirely, before this one's own `await fetchProgetto` below has resolved. `owner` is claimed by
// js/main.js SYNCHRONOUSLY, before either page's own dynamic `import()` even starts (a cold
// `import("./progetto.js")` measurably resolves slower than an already-warm `import("./progetti.
// js")`, so claiming it only once EXECUTION reaches here would let a navigation requested EARLIER
// but resolved LATER win). Checked BEFORE touching the DOM at all, not just after the `await`
// below: by the time THIS function's own (possibly slow) dynamic import finally resolves, a
// later, faster-resolving navigation may already have reclaimed `root` for itself -- clearing it
// and writing even the first, synchronous part of this page (the back-link) would still stomp on
// that newer page's already-finished render.
export async function renderProgetto(root, { progettoId, params = {}, owner } = {}) {
  if (root._smOwner !== owner) return;
  clear(root);
  root.append(el("a", { class: "pd-back", href: "#/progetti", text: "← Tutti i progetti" }));

  let progetto;
  try {
    progetto = await fetchProgetto(progettoId);
  } catch (error) {
    if (root._smOwner !== owner) return;
    root.append(el("p", { class: "pd-error", role: "alert", text: error.message || "Progetto non trovato." }));
    return;
  }
  if (root._smOwner !== owner) return;

  const head = el("div", { class: "pd-head" });
  const actionsHost = el("div", { class: "pd-head-actions" });
  const elementiHost = el("div", { class: "pd-elementi-host" });
  root.append(head, actionsHost, elementiHost);

  function buildField(def) {
    const value = progetto[def.key];
    const wrap = el("div", { class: "pd-field", "data-key": def.key });
    const errorEl = el("p", { class: "pd-field-error", role: "alert", hidden: true });

    function renderView() {
      clear(wrap);
      wrap.append(
        el("span", { class: "pd-field-label", text: def.label }),
        el("p", { class: "pd-field-value", text: value || "—" }),
        el("button", { type: "button", class: "pd-field-edit", text: "Modifica", "aria-label": `Modifica ${def.label}`, onclick: renderEdit }),
      );
    }

    function renderEdit() {
      clear(wrap);
      const input = def.multiline
        ? el("textarea", { id: `pd-field-${def.key}`, rows: "3" })
        : el("input", { type: "text", id: `pd-field-${def.key}`, required: def.required, maxlength: String(def.maxlength) });
      input.value = value || "";
      errorEl.hidden = true;
      const saveBtn = el("button", { type: "button", class: "pd-field-save", text: "Salva", onclick: () => save(input) });
      const cancelBtn = el("button", { type: "button", class: "pd-field-cancel", text: "Annulla", onclick: renderView });
      wrap.append(el("label", { class: "pd-field-label", for: `pd-field-${def.key}`, text: def.label }), input, saveBtn, cancelBtn, errorEl);
      input.focus();
    }

    async function save(input) {
      const next = input.value.trim();
      if (def.required && !next) {
        errorEl.textContent = "Campo obbligatorio.";
        errorEl.hidden = false;
        return;
      }
      const body = Object.fromEntries(FIELD_DEFS.map((f) => [f.key, f.key === def.key ? next : progetto[f.key]]));
      body.revisione = progetto.revisione;
      try {
        const result = await updateProgetto(progettoId, body);
        if (result.conflict) {
          errorEl.textContent = result.message || "Modificato da un altro utente: ricarica e riprova.";
          errorEl.hidden = false;
          return;
        }
        progetto = result.data;
        notifyProgettiChanged();
        renderHead();
      } catch (error) {
        errorEl.textContent = error.message || "Impossibile salvare.";
        errorEl.hidden = false;
      }
    }

    renderView();
    return wrap;
  }

  function renderHead() {
    clear(head);
    head.append(...FIELD_DEFS.map(buildField));
  }
  renderHead();

  const exportStatus = el("p", { class: "pd-export-status", role: "status" });
  const exportBtn = el("button", {
    type: "button",
    class: "pd-action",
    text: "Esporta",
    onclick: async () => {
      exportStatus.textContent = "";
      try {
        const payload = await fetchExportPayload(progettoId);
        downloadJson(`${safeFileName(progetto.nome)}.json`, payload);
      } catch (error) {
        exportStatus.textContent = error.message || "Impossibile esportare il progetto.";
      }
    },
  });
  const relazioneBtn = el("button", {
    type: "button",
    class: "pd-action pd-action--primary",
    text: "Relazione di progetto",
    onclick: () => openRelazioneProgetto(progetto),
  });
  actionsHost.append(exportBtn, relazioneBtn, exportStatus);

  renderProgettoElementi(elementiHost, { progetto, params });
}
