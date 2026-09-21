// One row of the registro list (WORKBENCH_SPEC §13.1): a collapsed line (state mark, titolo,
// tipo, sigla chips, clausola) that expands into "Il foglio" vs "Lo strumento", cella, impatto,
// the outputs affected, the sign-off form, the last decision and a "Storia" disclosure. No shared
// state: `onChanged(updatedEntry)` is the row's only way out, called once the SERVER confirms a
// sign-off -- the row never repaints itself optimistically ahead of that.
import { el, clear } from "./dom.js";
import { siglaChip } from "./nav-state.js";
import { signoff, fetchDivergenza } from "./registro-api.js";
import { resolveOutputLabels } from "./registro-outputs.js";
import { buildSignoffForm } from "./registro-signoff.js";
import { symbolNode } from "./symbols.js";
import { formatUnit } from "./format.js";

export const STATE_LABELS = { da_confermare: "○ Da confermare", approvato: "✓ Approvata", respinto: "✕ Respinta" };
export const TIPO_LABELS = {
  errore_foglio: "Errore del foglio",
  aggiornamento_normativo: "Aggiornamento normativo",
  scelta_ingegneristica: "Scelta ingegneristica",
  da_verificare: "Da verificare",
};

function toolChips(strumenti, toolsByName) {
  return el(
    "span",
    { class: "reg-row-tools" },
    strumenti.map((name) => {
      const tool = toolsByName.get(name);
      const chip = siglaChip(tool ? tool.sigla : name.slice(0, 2).toUpperCase());
      return el("a", { class: "reg-tool-link", href: `#/${encodeURIComponent(name)}`, title: tool ? tool.title : name }, [chip]);
    })
  );
}

function formatDate(iso) {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleDateString("it-IT");
}

function outputsLine(entry) {
  const PREFIX = "Risultati interessati: ";
  const p = el("p", { class: "reg-outputs", text: PREFIX + (entry.uscite.length > 0 ? entry.uscite.join(", ") : "—") });
  if (entry.uscite.length > 0) {
    resolveOutputLabels(entry.strumenti, entry.uscite).then((labels) => {
      clear(p);
      p.append(PREFIX);
      labels.forEach((item, index) => {
        if (index > 0) p.append(", ");
        if (item.symbol) p.append(symbolNode(item.symbol), " ");
        p.append(item.label);
        if (item.unit && item.unit !== "-") p.append(` [${formatUnit(item.unit)}]`);
      });
    });
  }
  return p;
}

// Excel-mode line (WORKBENCH_SPEC §13.1, `ramo`): whether/how the Excel-compatible mode
// reproduces THIS entry, always shown (distinct from -- and in addition to -- `outputsLine`
// above, which is shown regardless of `ramo` too).
// - "codice": a `legacy(id, legacy_compat)` branch of its own -> "Riprodotta in modalità Excel".
// - "condiviso": reproduced, but through another entry's branch (`riprodotta_da`, linked back into
//   the register) or a shared rules table -> the same sentence + why, as a muted note.
// - "nessuno": Excel mode does NOT reproduce it -- warn ink + icon, since such an entry never
//   appears in "Confronta con Excel" (js/confronto.js only ever diffs what both modes computed).
function buildExcelModeNode(entry) {
  if (entry.ramo === "codice") {
    return el("p", { class: "reg-excel-mode", text: "Riprodotta in modalità Excel" });
  }
  if (entry.ramo === "condiviso") {
    const line = el("p", { class: "reg-excel-mode" });
    if (entry.riprodotta_da.length > 0) {
      line.append("Riprodotta in modalità Excel insieme a ");
      entry.riprodotta_da.forEach((id, index) => {
        if (index > 0) line.append(", ");
        line.append(el("a", { href: `#/registro?id=${encodeURIComponent(id)}`, text: id }));
      });
    } else {
      line.append("Riprodotta in modalità Excel");
    }
    return el("div", { class: "reg-excel-mode-wrap" }, [line, el("p", { class: "reg-excel-mode-note", text: entry.motivo_senza_ramo })]);
  }
  return el("p", { class: "reg-excel-mode reg-excel-mode--none" }, [
    el("span", { class: "reg-excel-mode-icon", "aria-hidden": "true", text: "⚠" }),
    document.createTextNode(` NON riprodotta in modalità Excel: ${entry.motivo_senza_ramo}`),
  ]);
}

function decisionText(record) {
  return record.nota ? `${record.sigla} · ${formatDate(record.data)} · ${record.nota}` : `${record.sigla} · ${formatDate(record.data)}`;
}

function buildHistory(entry) {
  const body = el("div", { class: "reg-history-body" });
  const details = el("details", { class: "reg-history" }, [el("summary", { text: "Storia" }), body]);
  let loaded = false;
  details.addEventListener("toggle", () => {
    if (!details.open || loaded) return;
    loaded = true;
    body.textContent = "Caricamento…";
    fetchDivergenza(entry.id)
      .then((full) => {
        clear(body);
        const storia = full.storia || [];
        if (storia.length === 0) {
          body.append(el("p", { class: "reg-history-empty", text: "Nessuna decisione precedente." }));
          return;
        }
        const list = el("ul", { class: "reg-history-list" });
        for (const record of storia) list.append(el("li", { text: `${STATE_LABELS[record.stato] || record.stato} · ${decisionText(record)}` }));
        body.append(list);
      })
      .catch((error) => {
        clear(body);
        body.append(el("p", { class: "reg-history-empty", text: error.message || "Impossibile caricare la storia." }));
      });
  });
  return details;
}

// `checkbox`: an optional pre-built bulk-selection `<input type=checkbox>` prepended to the row
// (registro.js owns the selection set; this module never sees it). `onChanged` fires with the
// updated entry after a successful sign-off, so the caller can refresh totals/group counts.
export function buildRegistroRow(entry, { toolsByName, checkbox, onChanged } = {}) {
  let current = entry;
  const bodyId = `reg-body-${current.id.replace(/[^a-z0-9]/gi, "-")}`;

  const stateEl = el("span", { class: `reg-state reg-state--${current.stato}`, text: STATE_LABELS[current.stato] || current.stato });
  const toggle = el("button", { type: "button", class: "reg-row-toggle", "aria-expanded": "false", "aria-controls": bodyId }, [
    stateEl,
    el("span", { class: "reg-row-title", title: current.titolo, text: current.titolo }),
    el("span", { class: "reg-row-tipo", text: TIPO_LABELS[current.tipo] || current.tipo }),
    el("span", { class: "reg-row-clausola", text: current.clausola || "" }),
  ]);
  const head = el("div", { class: "reg-row-head" }, [...(checkbox ? [checkbox] : []), toggle, toolChips(current.strumenti, toolsByName)]);
  const body = el("div", { class: "reg-row-body", id: bodyId, hidden: true });
  const li = el("li", { class: "reg-row", "data-id": current.id }, [head, body]);

  let bodyBuilt = false;
  let formHost = null;
  let decisionHost = null;

  function applyState() {
    stateEl.className = `reg-state reg-state--${current.stato}`;
    stateEl.textContent = STATE_LABELS[current.stato] || current.stato;
  }

  function updateDecisionLine() {
    clear(decisionHost);
    if (current.data) decisionHost.append(el("p", { class: "reg-last-decision", text: decisionText(current) }));
  }

  // Builds the form ONCE per expand, not after every successful save: rebuilding it there would
  // replace the very `role=status` confirmation node (registro-signoff.js) the engineer's own
  // submit just populated, before they ever get to see it. A saved decision only updates the
  // state mark + the decision line in place; the form itself is left exactly as submitted.
  function renderForm() {
    clear(formHost);
    updateDecisionLine();
    const { form } = buildSignoffForm({
      idPrefix: bodyId,
      initial: current,
      onSubmit: (payload) =>
        signoff(current.id, payload).then((record) => {
          current = { ...current, stato: record.stato, sigla: record.sigla, nota: record.nota, data: record.data };
          applyState();
          updateDecisionLine();
          if (onChanged) onChanged(current);
        }),
    });
    formHost.append(form);
  }

  function buildBody() {
    clear(body);
    body.append(
      el("div", { class: "reg-compare" }, [
        el("div", { class: "reg-compare-col" }, [el("h4", { text: "Il foglio" }), el("p", { text: current.foglio })]),
        el("div", { class: "reg-compare-col" }, [el("h4", { text: "Lo strumento" }), el("p", { text: current.corretto })]),
      ])
    );
    if (current.cella) body.append(el("p", { class: "reg-cella", text: `Cella: ${current.cella}` }));
    if (current.impatto) body.append(el("p", { class: "reg-impatto", text: `Impatto: ${current.impatto}` }));
    body.append(outputsLine(current));
    body.append(buildExcelModeNode(current));
    formHost = el("div", { class: "reg-form-host" });
    decisionHost = el("div", { class: "reg-decision-host" });
    body.append(decisionHost, formHost);
    renderForm();
    body.append(buildHistory(current));
  }

  function setOpen(open) {
    toggle.setAttribute("aria-expanded", String(open));
    body.hidden = !open;
    if (open && !bodyBuilt) {
      bodyBuilt = true;
      buildBody();
    }
  }

  toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));

  return { li, open: () => setOpen(true) };
}
