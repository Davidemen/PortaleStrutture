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

// js/progetto-tabella-dati.js's `filterRows` reads this to answer "is this row da_ricalcolare /
// provvisorio / provvisorio_origine" for the `stato=...` filter -- the table itself never imports
// the stato payload shape directly, same reasoning as `renderProgettoStatoBadges` below.
export function statoElementiSnapshot() {
  return snapshot.elementi;
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

// §25.2/§25.4: "◐ Provvisorio" links to the registro filtered on the OWN tool; a chip alone
// leaves the engineer to go find the divergence by hand.
function linkRegistro(elemento) {
  return el("a", { class: "pst-chip-link", href: `#/registro?strumento=${encodeURIComponent(elemento.strumento)}`, text: "registro" });
}

// §25.4 says "Apri l'origine <sigla>" -- the SIGLA (a tool's short abbreviation), never the raw
// `strumento` slug: `toolsByName` is the same `Map<name, tool>` js/progetto-elementi.js already
// builds from `fetchTools()` (its own `tool.sigla`); missing/not-yet-loaded falls back to the
// slug rather than breaking the badge.
function siglaOf(toolsByName, strumento) {
  const tool = toolsByName && toolsByName.get(strumento);
  return tool ? tool.sigla : strumento;
}

// §25.4: "◐ Provvisorio per origine" links to each provider element that IS itself provvisorio --
// `motivi_origine[].elemento_id`/`strumento` (propagazione.py's own MotivoProvvisorio).
function linksFornitori(voce, toolsByName) {
  const seen = new Set();
  const motivi = (voce.motivi_origine || []).filter((m) => m.elemento_id && !seen.has(m.elemento_id) && seen.add(m.elemento_id));
  return motivi.map((m) =>
    el("a", { class: "pst-chip-link", href: `#/${encodeURIComponent(m.strumento)}?elemento=${encodeURIComponent(m.elemento_id)}`, text: `Apri l'origine ${siglaOf(toolsByName, m.strumento)}` }),
  );
}

// Called with the SAVED `elemento` row -- looks up its own state in the last-fetched `stato`
// snapshot (missing entirely, e.g. the stato fetch failed, means no badge rather than an error:
// the table itself must not fail because of it). `toolsByName` is optional (falls back to the
// raw slug in every sigla-shaped text above) so existing callers/tests keep working untouched.
export function renderProgettoStatoBadges(cell, elemento, toolsByName) {
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
    cell.append(el("span", { class: "pst-chip pst-chip--provvisorio", title: parts.join(", ") }, [
      document.createTextNode("◐ Provvisorio "),
      linkRegistro(elemento),
    ]));
  }
  if (voce.provvisorio_origine) {
    cell.append(el("span", { class: "pst-chip pst-chip--provvisorio", title: motiviProvvisorioOrigine(voce).join(" · ") }, [
      document.createTextNode("◐ Provvisorio per origine "),
      ...linksFornitori(voce, toolsByName).flatMap((a, i) => (i === 0 ? [a] : [document.createTextNode(" · "), a])),
    ]));
  }
}

// `[key, icon, word, query]` -- icon before the number before the word ("✓ 9 verificati"), per
// §25.4. `query` is the table's own filter key/value (progetto-tabella-dati.js's `filterRows`);
// `esito=...` was already wired, `stato=...` (below) drives the new da_ricalcolare/provvisorio/
// provvisorio_origine filters.
const CONTEGGI_LABELS = [
  ["elementi", "", "elementi", null],
  ["verificati", "✓", "verificati", "esito=verificato"],
  ["non_verificati", "✕", "non verificati", "esito=non_verificato"],
  ["dati_modificati", "○", "dati modificati", "esito=dati_modificati"],
  ["da_ricalcolare", "↻", "da ricalcolare", "stato=da_ricalcolare"],
  ["provvisori", "◐", "provvisori", "stato=provvisorio"],
  ["provvisori_per_origine", "◐", "provvisori per origine", "stato=provvisorio_origine"],
];

// `strutture:progetto-filtro` (same "module-decoupled, event-driven" pattern as js/registro.js's
// own `strutture:registro-changed`): js/progetto-tabella.js listens for this instead of the head
// counts calling into it directly, so the two can be mounted/wired independently by
// js/progetto-elementi.js without either importing the other.
function dispatchFiltro(query) {
  const [key, value] = query.split("=");
  document.dispatchEvent(new CustomEvent("strutture:progetto-filtro", { detail: { [key]: value } }));
}

// One line of counts under the project head (§25.4): "12 elementi · ✓ 9 verificati · ...". Each
// entry with a filter query becomes a `<button>` that merges that ONE key into the table's
// existing filter state (never replaces it -- Esc in the table clears everything back to
// defaults, see js/progetto-tabella.js).
export function renderProgettoStatoHead(host, conteggi) {
  clear(host);
  if (!conteggi) return;
  const parts = [];
  for (const [key, icon, word, query] of CONTEGGI_LABELS) {
    const value = conteggi[key];
    if (key !== "elementi" && !value) continue;
    const text = key === "elementi" ? `${value} elementi` : `${icon} ${value} ${word}`;
    if (query) {
      parts.push(el("button", { type: "button", class: "pst-head-count", text, onclick: () => dispatchFiltro(query) }));
    } else {
      parts.push(el("span", { class: "pst-head-count pst-head-count--static", text }));
    }
  }
  if (conteggi.controllo_rinviato) parts.push(el("span", { class: "pst-head-count pst-head-count--static", text: "Controllo rinviato" }));
  if (conteggi.cicli_origini) parts.push(el("span", { class: "pst-head-count pst-head-count--static", text: `⟲ ${conteggi.cicli_origini} cicli di origini` }));
  host.append(el("p", { class: "pst-head-line" }, parts.flatMap((node, index) => (index === 0 ? [node] : [document.createTextNode(" · "), node]))));
}
