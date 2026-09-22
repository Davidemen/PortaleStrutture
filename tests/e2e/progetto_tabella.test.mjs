// Pure row model / sort / filter / footer (js/progetto-tabella-dati.js, WORKBENCH_SPEC §20.2).
import test from "node:test";
import assert from "node:assert/strict";
import { buildRows, filterRows, sortRows, footerCounts, SORT_DEFAULT } from "../../src/strutture/web/static/js/progetto-tabella-dati.js";

function elemento(overrides = {}) {
  return {
    id: "e1", strumento: "muro-sostegno", nome: "Muro 1", stato: "verificato",
    sintesi: { eta_max: 0.5, avvisi: { n: 0, primo: "" } },
    aggiornato: "2026-01-01T10:00:00Z", revisione: 1, eliminato: null,
    ...overrides,
  };
}

const toolsByName = new Map([["muro-sostegno", { sigla: "MUR", title: "Muro di sostegno" }]]);

test("buildRows skips soft-deleted elements and reads sintesi.eta_max/avvisi", () => {
  const rows = buildRows([elemento(), elemento({ id: "e2", eliminato: "2026-01-02T00:00:00Z" })], toolsByName);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].etaMax, 0.5);
  assert.equal(rows[0].avvisi.n, 0);
  assert.equal(rows[0].avvisi.nd, false);
});

test("buildRows shows n.d. avvisi for an element saved before §20.1", () => {
  const rows = buildRows([elemento({ sintesi: { eta_max: 0.5 } })], toolsByName);
  assert.equal(rows[0].avvisi.nd, true);
  assert.equal(rows[0].avvisi.n, null);
});

test("a failed run's sintesi.errore reads as esitoKey 'errore'", () => {
  const rows = buildRows([elemento({ stato: "non_verificato", sintesi: { errore: "Dati non validi." } })], toolsByName);
  assert.equal(rows[0].esitoKey, "errore");
});

test("sortRows on eta puts missing values last regardless of direction", () => {
  const rows = buildRows([
    elemento({ id: "a", sintesi: { eta_max: 0.3 } }),
    elemento({ id: "b", sintesi: {} }),
    elemento({ id: "c", sintesi: { eta_max: 0.9 } }),
  ], toolsByName);
  const desc = sortRows(rows, "eta", "desc").map((r) => r.id);
  assert.deepEqual(desc, ["c", "a", "b"]);
  const asc = sortRows(rows, "eta", "asc").map((r) => r.id);
  assert.deepEqual(asc, ["a", "c", "b"]);
});

test("sortRows never mutates its input array", () => {
  const rows = buildRows([elemento({ id: "a" }), elemento({ id: "b", nome: "Aardvark" })], toolsByName);
  const copy = [...rows];
  sortRows(rows, "nome", "asc");
  assert.deepEqual(rows, copy);
});

test("filterRows: esito, strumento, soloAvvisi and accent/case-insensitive q all combine", () => {
  const rows = buildRows([
    elemento({ id: "a", nome: "Muro Città", sintesi: { eta_max: 0.4, avvisi: { n: 2, primo: "x" } } }),
    elemento({ id: "b", nome: "Muro Nord", strumento: "altro", stato: "non_verificato", sintesi: {} }),
  ], toolsByName);
  assert.deepEqual(filterRows(rows, { soloAvvisi: true }).map((r) => r.id), ["a"]);
  assert.deepEqual(filterRows(rows, { esito: "non_verificato" }).map((r) => r.id), ["b"]);
  assert.deepEqual(filterRows(rows, { strumento: "muro-sostegno" }).map((r) => r.id), ["a"]);
  assert.deepEqual(filterRows(rows, { q: "citta" }).map((r) => r.id), ["a"]);
});

test("footerCounts totals esiti and finds the governing eta max", () => {
  const rows = buildRows([
    elemento({ id: "a", sintesi: { eta_max: 0.4 } }),
    elemento({ id: "b", stato: "non_verificato", sintesi: { eta_max: 0.9 } }),
  ], toolsByName);
  const counts = footerCounts(rows);
  assert.equal(counts.totale, 2);
  assert.equal(counts.verificato, 1);
  assert.equal(counts.non_verificato, 1);
  assert.equal(counts.etaMaxProgetto, 0.9);
});

test("SORT_DEFAULT is aggiornato/desc, as the old list rendering", () => {
  assert.deepEqual(SORT_DEFAULT, { ordina: "aggiornato", verso: "desc" });
});
