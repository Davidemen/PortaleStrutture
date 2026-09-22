// Pure state for "Varianti affiancate" (WORKBENCH_SPEC §19.1): the client-side working set kept
// in `sessionStorage` (never SQLite -- see §19.1's own reasoning). Every function here takes a
// `set` (`{attiva, varianti: [{id, nome, inputs, origine}]}` or `null`) and returns a NEW one,
// immutable throughout -- node-testable, no DOM access. `js/varianti-bar.js`/
// `js/varianti-confronto.js` own persistence (`caricaVarianti`/`salvaVarianti`/`chiudiVarianti`
// below) and every DOM/event concern.
import { readSessionJSON, writeSessionJSON, removeSession } from "./storage.js";

export const MAX_VARIANTI = 4;
const LETTERE = ["A", "B", "C", "D"];
const NOME_MAX_CHARS = 40;

function storageKey(tool) {
  return `sm.varianti.${tool}`;
}

export function caricaVarianti(tool) {
  return readSessionJSON(storageKey(tool), null);
}

export function salvaVarianti(tool, set) {
  return writeSessionJSON(storageKey(tool), set);
}

export function chiudiVarianti(tool) {
  removeSession(storageKey(tool));
}

function prossimaLettera(set) {
  const usate = new Set(set.varianti.map((variante) => variante.id));
  return LETTERE.find((lettera) => !usate.has(lettera)) || null;
}

function clonaInputs(inputs) {
  // A plain deep clone via JSON round-trip: every field value here is already JSON-serialisable
  // (scalars, tables, lists -- the same shape `form-state.js` itself persists), so this is exact
  // and immutable without needing a per-kind clone rule.
  return JSON.parse(JSON.stringify(inputs ?? {}));
}

export function trovaVariante(set, id) {
  return set ? set.varianti.find((variante) => variante.id === id) || null : null;
}

export function varianteAttiva(set) {
  return trovaVariante(set, set ? set.attiva : null);
}

export function puoAggiungere(set) {
  return !set || set.varianti.length < MAX_VARIANTI;
}

// "Crea variante", first press (§19.2): turns the current form into A and a copy into B, B active.
export function iniziaVarianti(inputsCorrenti, origine = null) {
  const a = { id: "A", nome: "A", inputs: clonaInputs(inputsCorrenti), origine };
  const b = { id: "B", nome: "B", inputs: clonaInputs(inputsCorrenti), origine: null };
  return { attiva: "B", varianti: [a, b] };
}

// "Crea variante", later presses: copies the ACTIVE variant into a new one, which becomes active.
export function aggiungiVariante(set) {
  if (!puoAggiungere(set)) return set;
  const lettera = prossimaLettera(set);
  if (!lettera) return set;
  const attiva = varianteAttiva(set);
  const nuova = { id: lettera, nome: lettera, inputs: clonaInputs(attiva ? attiva.inputs : {}), origine: null };
  return { attiva: lettera, varianti: [...set.varianti, nuova] };
}

// Per-tab "Duplica": same copy as `aggiungiVariante`, but from an explicit variant, not
// necessarily the active one.
export function duplicaVariante(set, id) {
  if (!puoAggiungere(set)) return set;
  const sorgente = trovaVariante(set, id);
  if (!sorgente) return set;
  const lettera = prossimaLettera(set);
  if (!lettera) return set;
  const nuova = { id: lettera, nome: lettera, inputs: clonaInputs(sorgente.inputs), origine: null };
  return { attiva: lettera, varianti: [...set.varianti, nuova] };
}

export function attivaVariante(set, id) {
  if (!trovaVariante(set, id)) return set;
  return { ...set, attiva: id };
}

export function rinominaVariante(set, id, nome) {
  const pulito = String(nome ?? "").trim().slice(0, NOME_MAX_CHARS);
  const nomeFinale = pulito || id;
  return {
    ...set,
    varianti: set.varianti.map((variante) => (variante.id === id ? { ...variante, nome: nomeFinale } : variante)),
  };
}

// Every valid form change (§19.2 "Every valid form change updates the active variant's inputs").
export function aggiornaInputsVariante(set, id, inputs) {
  return {
    ...set,
    varianti: set.varianti.map((variante) => (variante.id === id ? { ...variante, inputs: clonaInputs(inputs) } : variante)),
  };
}

// Not allowed on the last remaining variant (§19.2) -- callers check `set.varianti.length > 1`
// before offering "Elimina" at all; this still refuses defensively.
export function eliminaVariante(set, id) {
  if (set.varianti.length <= 1) return set;
  const varianti = set.varianti.filter((variante) => variante.id !== id);
  const attiva = set.attiva === id ? varianti[0].id : set.attiva;
  return { attiva, varianti };
}

export function etichettaTab(variante) {
  return variante.nome && variante.nome !== variante.id ? `${variante.id} · ${variante.nome}` : variante.id;
}
