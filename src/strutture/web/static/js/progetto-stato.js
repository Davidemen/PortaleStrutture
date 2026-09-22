// `GET /api/progetti/{id}/stato` (WORKBENCH_SPEC §25.3/§25.4): fetch once per project-page render,
// then per-row chips ("↻ Da ricalcolare", "◐ Provvisorio", "◐ Provvisorio per origine") plus the
// project head's one-line counts. Icon + word, never colour alone (rule 4); every chip is plain
// text with a `title` tooltip (no popover component needed for this first cut).
import { el, clear } from "./dom.js";

async function readJson(response) {
  try {
    return await response.json();
  } catch (error) {
    throw new Error("Risposta del server non valida.");
  }
}

export async function fetchStatoProgetto(progettoId) {
  let response;
  try {
    response = await fetch(`/api/progetti/${encodeURIComponent(progettoId)}/stato`);
  } catch (error) {
    throw new Error("Impossibile contattare il server.");
  }
  const body = await readJson(response);
  if (response.status !== 200) {
    throw new Error((body.errors && body.errors[0]) || "Impossibile caricare lo stato del progetto.");
  }
  return body; // {elementi: {<id>: {...}}, conteggi: {...}}
}

// Module-level snapshot, set once per project-page render by js/progetto-elementi.js right after
// `fetchStatoProgetto` resolves -- js/progetto-tabella.js reads it synchronously while building
// each row (same "session" pattern as js/provenienza.js), so the table never has to thread the
// whole stato payload through every function call.
let snapshot = { elementi: {}, conteggi: null };

export function setStatoProgetto(data) {
  snapshot = data && data.elementi ? data : { elementi: {}, conteggi: null };
}

export function statoConteggi() {
  return snapshot.conteggi;
}

function motiviRicalcolo(voce) {
  const propri = voce.motivi.filter((m) => m.causa !== "origine_da_ricalcolare" && m.causa !== "ciclo_origini" && m.causa !== "controllo_rinviato");
  if (propri.length > 0) return propri.map((m) => m.messaggio || `${m.chiave} da ${m.strumento}: ${m.valore_salvato} → ${m.valore_attuale}`);
  return voce.motivi.map((m) => m.messaggio || m.causa);
}

function motiviProvvisorioOrigine(voce) {
  return (voce.motivi_origine || []).map((m) => (m.causa === "origine_excel"
    ? `Usa valori di ${m.strumento}, che riproduce il foglio Excel`
    : `Usa valori di ${m.strumento}, che applica correzioni non approvate`));
}

// Called with the SAVED `elemento` row -- looks up its own state in the last-fetched `stato`
// snapshot (missing entirely, e.g. the stato fetch failed, means no badge rather than an error:
// the table itself must not fail because of it).
export function renderProgettoStatoBadges(cell, elemento) {
  clear(cell);
  const voce = snapshot.elementi[elemento.id];
  if (!voce) return;
  if (voce.da_ricalcolare) {
    cell.append(el("span", { class: "pst-chip pst-chip--ricalcola", title: motiviRicalcolo(voce).join(" · "), text: "↻ Da ricalcolare" }));
  }
  if (voce.provvisorio) {
    const da = voce.correzioni.da_confermare;
    const respinto = voce.correzioni.respinto;
    const dubbi = voce.correzioni.da_verificare;
    const parts = [`Il calcolo applica correzioni del registro non ancora approvate (${da} da confermare, ${respinto} respinte)`];
    if (dubbi) parts.push(`${dubbi} dubbi da verificare`);
    cell.append(el("span", { class: "pst-chip pst-chip--provvisorio", title: parts.join(", "), text: "◐ Provvisorio" }));
  }
  if (voce.provvisorio_origine) {
    cell.append(el("span", { class: "pst-chip pst-chip--provvisorio", title: motiviProvvisorioOrigine(voce).join(" · "), text: "◐ Provvisorio per origine" }));
  }
}

const CONTEGGI_LABELS = [
  ["elementi", "elementi", null],
  ["verificati", "✓ verificati", "esito=verificato"],
  ["non_verificati", "✕ non verificati", "esito=non_verificato"],
  ["dati_modificati", "○ dati modificati", "esito=dati_modificati"],
  ["da_ricalcolare", "↻ da ricalcolare", null],
  ["provvisori", "◐ provvisori", null],
  ["provvisori_per_origine", "◐ provvisori per origine", null],
];

// One line of counts under the project head (§25.4): "12 elementi · ✓ 9 verificati · ...". Each
// entry with a filter query becomes a `<button>` that calls `onFiltra(query)` -- js/progetto-
// tabella.js's own `state`/`syncQuery` shape (`esito=...`); the two propagated counts have no
// table column to filter by yet, so they render as plain text for this first cut.
export function renderProgettoStatoHead(host, conteggi, onFiltra) {
  clear(host);
  if (!conteggi) return;
  const parts = [];
  for (const [key, label, query] of CONTEGGI_LABELS) {
    const value = conteggi[key];
    if (key !== "elementi" && !value) continue;
    const text = key === "elementi" ? `${value} elementi` : `${value} ${label}`;
    if (query && onFiltra) {
      parts.push(el("button", { type: "button", class: "pst-head-count", text, onclick: () => onFiltra(query) }));
    } else {
      parts.push(el("span", { class: "pst-head-count pst-head-count--static", text }));
    }
  }
  if (conteggi.controllo_rinviato) parts.push(el("span", { class: "pst-head-count pst-head-count--static", text: "Controllo rinviato" }));
  if (conteggi.cicli_origini) parts.push(el("span", { class: "pst-head-count pst-head-count--static", text: `⟲ ${conteggi.cicli_origini} cicli di origini` }));
  host.append(el("p", { class: "pst-head-line" }, parts.flatMap((node, index) => (index === 0 ? [node] : [document.createTextNode(" · "), node]))));
}
