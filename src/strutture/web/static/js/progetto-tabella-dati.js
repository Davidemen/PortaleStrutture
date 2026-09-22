// Pure row model, sort and filter for the project table (WORKBENCH_SPEC §20.2). No DOM here --
// node-testable straight from `tests/e2e/progetto_tabella.test.mjs`. Every function returns a NEW
// array/object; nothing here mutates its arguments.
export const ESITO_LABELS = {
  verificato: "✓ Verificato",
  non_verificato: "✕ Non verificato",
  dati_modificati: "○ Dati modificati",
  errore: "! Errore di calcolo",
};

function normalizza(text) {
  return String(text || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

// `elemento.sintesi.errore` (§20.1) means the last run failed outright -- shown as "! Errore di
// calcolo" rather than the plain `stato` word, which the backend still stores as
// "non_verificato" for a failed run (no dedicated `stato` value for it).
function esitoKey(elemento) {
  if (elemento.sintesi && elemento.sintesi.errore) return "errore";
  return elemento.stato;
}

// `avvisi` is `undefined` for elements saved before §20.1 ("n.d."); `null` fields inside it are
// never produced by the backend but tolerated defensively.
function avvisiInfo(elemento) {
  const avvisi = elemento.sintesi && elemento.sintesi.avvisi;
  if (!avvisi || typeof avvisi.n !== "number") return { nd: true, n: null, primo: "" };
  return { nd: false, n: avvisi.n, primo: avvisi.primo || "" };
}

export function buildRows(elementi, toolsByName) {
  return elementi
    .filter((elemento) => !elemento.eliminato)
    .map((elemento) => {
      const tool = toolsByName.get(elemento.strumento);
      const eta = elemento.sintesi && typeof elemento.sintesi.eta_max === "number" ? elemento.sintesi.eta_max : null;
      const muted = elemento.stato === "dati_modificati";
      return {
        id: elemento.id,
        strumento: elemento.strumento,
        siglaTool: tool ? tool.sigla : elemento.strumento.slice(0, 2).toUpperCase(),
        toolTitle: tool ? tool.title : elemento.strumento,
        nome: elemento.nome,
        etaMax: eta,
        esitoKey: esitoKey(elemento),
        avvisi: avvisiInfo(elemento),
        aggiornato: elemento.aggiornato || "",
        revisione: elemento.revisione,
        muted,
        elemento,
      };
    });
}

// `stato`/`statoElementi` (§25.4): "da_ricalcolare" | "provvisorio" | "provvisorio_origine" against
// GET /api/progetti/{id}/stato's own per-elemento voce (js/progetto-stato.js's
// `statoElementiSnapshot()`) -- missing entirely (stato fetch still in flight/failed) never
// matches, same "no badge rather than an error" rule as `renderProgettoStatoBadges`.
export function filterRows(rows, { q = "", strumento = "", esito = "", soloAvvisi = false, stato = "", statoElementi = {} } = {}) {
  const needle = normalizza(q);
  return rows.filter((row) => {
    if (strumento && row.strumento !== strumento) return false;
    if (esito && row.esitoKey !== esito) return false;
    if (soloAvvisi && (row.avvisi.nd || !row.avvisi.n)) return false;
    if (stato) {
      const voce = statoElementi[row.id];
      if (!voce || !voce[stato]) return false;
    }
    if (!needle) return true;
    return normalizza(row.nome).includes(needle) || normalizza(row.siglaTool).includes(needle) || normalizza(row.toolTitle).includes(needle);
  });
}

// Rank, never the alphabet: an internal key like "errore" or "non_verificato" sorts
// alphabetically to a spot that has nothing to do with how bad the outcome is.
const ESITO_RANK = { errore: 0, non_verificato: 1, dati_modificati: 2, verificato: 3 };

const SORT_KEYS = {
  strumento: (row) => normalizza(row.toolTitle),
  nome: (row) => normalizza(row.nome),
  eta: (row) => row.etaMax,
  esito: (row) => (row.esitoKey in ESITO_RANK ? ESITO_RANK[row.esitoKey] : -1),
  avvisi: (row) => (row.avvisi.nd ? null : row.avvisi.n),
  aggiornato: (row) => row.aggiornato,
};

export const SORT_DEFAULT = { ordina: "aggiornato", verso: "desc" };

// Missing values (`null`/`undefined`/`""`) always sort last regardless of `verso`; stable
// secondary key is always the row's `nome`.
export function sortRows(rows, ordina, verso) {
  const key = SORT_KEYS[ordina] || SORT_KEYS.aggiornato;
  const sign = verso === "asc" ? 1 : -1;
  const indexed = rows.map((row, index) => ({ row, index }));
  indexed.sort((a, b) => {
    const va = key(a.row);
    const vb = key(b.row);
    const missingA = va === null || va === undefined || va === "";
    const missingB = vb === null || vb === undefined || vb === "";
    if (missingA && missingB) return normalizza(a.row.nome).localeCompare(normalizza(b.row.nome)) || a.index - b.index;
    if (missingA) return 1;
    if (missingB) return -1;
    if (va < vb) return -1 * sign;
    if (va > vb) return 1 * sign;
    return normalizza(a.row.nome).localeCompare(normalizza(b.row.nome)) || a.index - b.index;
  });
  return indexed.map((entry) => entry.row);
}

export function footerCounts(rows) {
  const conteggi = { totale: rows.length, verificato: 0, non_verificato: 0, dati_modificati: 0, errore: 0 };
  let etaMaxProgetto = null;
  let etaMaxRow = null;
  for (const row of rows) {
    if (conteggi[row.esitoKey] !== undefined) conteggi[row.esitoKey] += 1;
    if (row.etaMax !== null && (etaMaxProgetto === null || row.etaMax > etaMaxProgetto)) {
      etaMaxProgetto = row.etaMax;
      etaMaxRow = row;
    }
  }
  return { ...conteggi, etaMaxProgetto, etaMaxSigla: etaMaxRow ? etaMaxRow.siglaTool : null };
}
