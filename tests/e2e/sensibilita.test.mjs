// Pure-function unit tests for js/sensibilita-grafico.js (WORKBENCH_SPEC §24.2): the top-5
// selection, row mapping and guide builders. No DOM, no server:
//   node --test tests/e2e/sensibilita.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { selectTopChecks, buildRows, buildSeries, buildGuides, buildHGuides, MAX_SERIE } from "../../src/strutture/web/static/js/sensibilita-grafico.js";

function verifica(nome, eta, esito) {
  return { nome, clausola: "", eta, esito };
}

test("selectTopChecks puts a failed-somewhere check before a passing one", () => {
  const verifiche = [
    verifica("A", [0.3, 0.4], [true, true]),
    verifica("B", [0.9, 1.2], [true, false]),
  ];
  const top = selectTopChecks(verifiche, 2);
  assert.deepEqual(top.map((v) => v.nome), ["B", "A"]);
});

test("selectTopChecks orders ties by max eta and caps at the given max", () => {
  const verifiche = [
    verifica("A", [0.2], [true]),
    verifica("B", [0.9], [true]),
    verifica("C", [0.5], [true]),
  ];
  const top = selectTopChecks(verifiche, 2);
  assert.deepEqual(top.map((v) => v.nome), ["B", "C"]);
});

test("selectTopChecks never returns more than MAX_SERIE by default", () => {
  const verifiche = Array.from({ length: 8 }, (_, i) => verifica(`V${i}`, [i], [true]));
  assert.equal(selectTopChecks(verifiche).length, MAX_SERIE);
});

test("selectTopChecks drops outcome-only checks (no eta at all)", () => {
  const verifiche = [verifica("Solo esito", [null, null], [true, false])];
  assert.deepEqual(selectTopChecks(verifiche), []);
});

test("buildRows/buildSeries produce chart.js-shaped rows keyed s1..sN", () => {
  const checks = [verifica("A", [0.1, 0.2], [true, true]), verifica("B", [0.5, null], [true, null])];
  const rows = buildRows([10, 20], checks);
  assert.deepEqual(rows, [{ x: 10, s1: 0.1, s2: 0.5 }, { x: 20, s1: 0.2, s2: null }]);
  assert.deepEqual(buildSeries(checks).map((s) => s.key), ["s1", "s2"]);
});

test("buildGuides/buildHGuides are empty for a non-finite value", () => {
  assert.deepEqual(buildGuides(NaN), []);
  assert.deepEqual(buildGuides(500), [{ value: 500, label: "attuale" }]);
  assert.deepEqual(buildHGuides(undefined), []);
  assert.deepEqual(buildHGuides(1), [{ value: 1, label: "obiettivo 1" }]);
});
