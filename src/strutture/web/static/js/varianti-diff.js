// Pure diff helpers for "Affianca" (WORKBENCH_SPEC §19.3): input differences (incl. tables),
// relative deltas between a value and the reference column, and the union of check names across
// every variant's report. No DOM access -- node-testable with plain `node --test`
// (tests/e2e/varianti_diff.test.mjs).
import { sortChecks } from "./verdict.js";

const PERCENT_FORMAT = new Intl.NumberFormat("it-IT", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

function stable(value) {
  return JSON.stringify(value === undefined ? null : value);
}

export function sameValue(a, b) {
  return stable(a) === stable(b);
}

// Rows of a table/list field: how many row positions differ (index-wise), and how many rows the
// longer of the two has ("tabella: 2 righe diverse su 5", §19.3).
export function diffRighe(a, b) {
  const righeA = Array.isArray(a) ? a : [];
  const righeB = Array.isArray(b) ? b : [];
  const totale = Math.max(righeA.length, righeB.length);
  let diverse = 0;
  for (let i = 0; i < totale; i += 1) {
    if (!sameValue(righeA[i], righeB[i])) diverse += 1;
  }
  return { diverse, totale };
}

function isTableLike(field) {
  return field && (field.kind === "table" || field.kind === "list");
}

// One entry per field present in at least one variant's inputs, `diverso` true when at least two
// variants disagree on its value (§19.3 "Dati diversi: 3 di 24"). `dettaglio` carries the table
// row-diff summary for table/list fields, null otherwise.
export function differenzeCampi(fields, varianti) {
  const byName = new Map(fields.map((field) => [field.name, field]));
  const nomi = fields.map((field) => field.name);
  return nomi.map((nome) => {
    const field = byName.get(nome);
    const valori = varianti.map((variante) => (variante.inputs ? variante.inputs[nome] : undefined));
    const riferimento = valori[0];
    const diverso = valori.some((valore) => !sameValue(valore, riferimento));
    const dettaglio = diverso && isTableLike(field) ? diffRighe(riferimento, valori.find((v) => !sameValue(v, riferimento))) : null;
    return { field, nome, diverso, dettaglio };
  });
}

export function contaDatiDiversi(fields, varianti) {
  const differenze = differenzeCampi(fields, varianti);
  return { diverse: differenze.filter((voce) => voce.diverso).length, totale: differenze.length };
}

// Union of check names, ordered by `sortChecks` on the reference column; any check present ONLY
// in a later column (absent from the reference) is appended, in first-seen order (§19.3 point 4:
// "one row per check name in the union of all columns... a check absent from a column shows —").
export function unioneVerifiche(reportsPerVariante, indiceRiferimento = 0) {
  const riferimento = reportsPerVariante[indiceRiferimento];
  const nomi = [];
  const visti = new Set();
  const ordinati = riferimento ? sortChecks(riferimento.checks || []) : [];
  for (const check of ordinati) {
    if (!visti.has(check.name)) {
      visti.add(check.name);
      nomi.push(check.name);
    }
  }
  for (const report of reportsPerVariante) {
    if (!report) continue;
    for (const check of report.checks || []) {
      if (!visti.has(check.name)) {
        visti.add(check.name);
        nomi.push(check.name);
      }
    }
  }
  return nomi;
}

export function checkPer(report, nome) {
  if (!report || !Array.isArray(report.checks)) return null;
  return report.checks.find((check) => check.name === nome) || null;
}

// A number rounded to `decimali` decimals: the basis for "equal at displayed precision" (§19.3).
function arrotonda(valore, decimali) {
  const fattore = 10 ** decimali;
  return Math.round(valore * fattore) / fattore;
}

// Relative delta of `valore` against `riferimento` (§19.3: "▲ +12,5 %" / "▼ −3,0 %", 1 decimal;
// "= uguale" when equal at displayed precision). Returns null when either side is not a finite
// number or the reference is zero (a relative delta from zero is not meaningful).
export function deltaRelativo(valore, riferimento, { decimali = 1 } = {}) {
  if (typeof valore !== "number" || typeof riferimento !== "number") return null;
  if (!Number.isFinite(valore) || !Number.isFinite(riferimento)) return null;
  if (arrotonda(valore, decimali) === arrotonda(riferimento, decimali)) return { simbolo: "=", testo: "= uguale" };
  if (riferimento === 0) return null;
  const percento = ((valore - riferimento) / Math.abs(riferimento)) * 100;
  const arrotondata = arrotonda(percento, decimali);
  const simbolo = arrotondata >= 0 ? "▲" : "▼";
  const segno = arrotondata >= 0 ? "+" : "−"; // U+2212 minus sign, not a hyphen, per format.js convention
  const testo = `${simbolo} ${segno}${PERCENT_FORMAT.format(Math.abs(arrotondata))} %`;
  return { simbolo, testo };
}

// The Sintesi's η max (verdict.js `effectiveUtilisation`, already normalised so <=1 is safe) for
// a report with no governing check returns null -- callers show "—" in that case.
export function etaMaxDi(report) {
  if (!report || !Array.isArray(report.checks) || report.checks.length === 0) return null;
  const ordinati = sortChecks(report.checks);
  return ordinati[0] || null;
}
