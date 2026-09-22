// Pure-function unit tests for js/dimensiona-modello.js (WORKBENCH_SPEC §23.5): the Da/A prefill
// rule and the numeric-field filter used to build the "Campo" select. No DOM, no server:
//   node --test tests/e2e/dimensiona.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { campiNumerici, prefillRange, origineTesto, groupFields } from "../../src/strutture/web/static/js/dimensiona-modello.js";

test("campiNumerici keeps only numeric fields and drops legacy_compat", () => {
  const fields = [
    { name: "h_mm", kind: "number" },
    { name: "legacy_compat", kind: "boolean" },
    { name: "zona", kind: "enum" },
    { name: "tabella", kind: "table" },
  ];
  assert.deepEqual(campiNumerici(fields).map((f) => f.name), ["h_mm"]);
});

test("prefillRange: inclusive minimum/maximum are used as-is", () => {
  const field = { minimum: 100, maximum: 900 };
  assert.deepEqual(prefillRange(field, 500), { da: 100, a: 900 });
});

test("prefillRange: no bound falls back to current x0.5 / x2", () => {
  const field = {};
  assert.deepEqual(prefillRange(field, 500), { da: 250, a: 1000 });
});

test("prefillRange: exclusive bound never becomes the prefilled value itself", () => {
  const field = { exclusiveMin: 0 };
  const { da } = prefillRange(field, 10);
  assert.ok(da > 0);
  assert.equal(da, 5);
});

test("prefillRange: current value <= 0 leaves both sides empty and required", () => {
  assert.deepEqual(prefillRange({}, 0), { da: null, a: null });
  assert.deepEqual(prefillRange({}, -3), { da: null, a: null });
  assert.deepEqual(prefillRange({}, null), { da: null, a: null });
});

test("origineTesto matches the §23.1 provenance labels", () => {
  assert.equal(origineTesto("campo"), "Passo d'ufficio per questo campo");
  assert.equal(origineTesto("tipo"), "Passo d'ufficio per il tipo di dato");
  assert.equal(origineTesto("intero"), "Numero intero");
  assert.equal(origineTesto(null), "");
});

test("groupFields groups by the field's own group, unlabelled fields under Altro", () => {
  const fields = [
    { name: "a", group: "Geometria" },
    { name: "b", group: "Geometria" },
    { name: "c" },
  ];
  const groups = groupFields(fields);
  assert.deepEqual([...groups.keys()], ["Geometria", "Altro"]);
  assert.equal(groups.get("Geometria").length, 2);
  assert.equal(groups.get("Altro").length, 1);
});
