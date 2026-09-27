// Saved elements of an entry's parts -- WORKBENCH_SPEC §27.7. Tiny shared state between
// js/voce.js (which knows the entry) and js/elemento-salva.js (which saves the visible part):
// - `ricorda`/`ricordato`: the element each part is tied to, so switching the result tab (which
//   re-mounts the form for the other tool) keeps "Salva" pointing at that part's element;
// - `impostaCompagno`: with the optional part ticked, "Salva in progetto" saves TWO elements (one
//   per tool, " -1"/" -2" by part order) and "Salva" updates both with their own `revisione`.
// No DOM, no network: the caller passes the payload builder and does the requests.

const ricordati = new Map();
let compagno = null;
// Only an entry page remembers: a plain single-tool page reopened later must never find itself
// tied to an element it was not opened with.
let attivo = false;

export function ricorda(tool, loaded) {
  if (!attivo) return;
  if (loaded) ricordati.set(tool, loaded);
  else ricordati.delete(tool);
}

export function ricordato(tool) {
  return attivo ? ricordati.get(tool) || null : null;
}

// Called by js/voce.js on every route into an entry (fresh start) and on leaving it.
export function azzeraElementi(voceAperta) {
  ricordati.clear();
  compagno = null;
  attivo = voceAperta;
}

// `{ attiva, tool, titolo, indiceAttiva, indice, payload(nome, sigla, nota) -> Promise<body> }`
// or null (optional part unticked / not an entry page).
export function impostaCompagno(valore) {
  compagno = valore;
}

export function compagnoDi(tool) {
  return compagno && compagno.attiva === tool ? compagno : null;
}
