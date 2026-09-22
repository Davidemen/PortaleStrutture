// Pure matching of a sketch text to a Dati field (js/schizzo-modifica.js `campoPerTesto`): symbol
// AND unit must match a NUMBER field whose current value is the one shown; an explicit `campo`
// from the sketch wins for any existing number field.
import test from "node:test";
import assert from "node:assert/strict";
import { campoPerTesto } from "../../src/strutture/web/static/js/schizzo-modifica.js";

const FIELDS = [
  { name: "b", kind: "number", symbol: "b", unit: "m" },
  { name: "d", kind: "number", symbol: "d", unit: "m" },
  { name: "B_mm", kind: "number", symbol: "B", unit: "mm" },
  { name: "q_kN_m2", kind: "number", symbol: "q", unit: "kN/m2" },
  { name: "mu", kind: "number", symbol: "μ", unit: "" },
  { name: "zona", kind: "enum", symbol: "Z", unit: "" },
];
const VALUES = { b: 15, d: 12, B_mm: 1500, q_kN_m2: 2, mu: 0.8 };
const valoreDi = (name) => (name in VALUES ? VALUES[name] : null);
const opts = { valoreDi };

test("matches symbol, unit and the shown value of a number field", () => {
  assert.equal(campoPerTesto("b = 15,00 m", FIELDS, opts).name, "b");
  assert.equal(campoPerTesto("d = 12,00 m", FIELDS, opts).name, "d");
  assert.equal(campoPerTesto("μ = 0,80", FIELDS, opts).name, "mu"); // dimensionless
});

test("'kN/m²' in the drawing is the field's 'kN/m2'", () => {
  assert.equal(campoPerTesto("q = 2 kN/m²", FIELDS, opts).name, "q_kN_m2");
});

test("a shown value that is not the input's current value never links (a result label)", () => {
  assert.equal(campoPerTesto("b = 40,00 m", FIELDS, opts), null);
  assert.equal(campoPerTesto("q = 30 kN/m²", FIELDS, opts), null);
  assert.equal(campoPerTesto("b = 15,00 m", FIELDS, { valoreDi: null }), null); // no form: no guard, no link
});

test("a different unit, a non-number field or an unknown symbol give null", () => {
  assert.equal(campoPerTesto("B = 1,50 m", FIELDS, opts), null); // field is in mm, sketch in m
  assert.equal(campoPerTesto("Z = 2", FIELDS, opts), null); // enum
  assert.equal(campoPerTesto("H = 3,00 m", FIELDS, opts), null);
  assert.equal(campoPerTesto("", FIELDS, opts), null);
  assert.equal(campoPerTesto("vento", FIELDS, opts), null);
});

test("an explicit `campo` from the sketch wins, but only for an existing number field", () => {
  assert.equal(campoPerTesto("B = 1,50 m", FIELDS, { campo: "B_mm", valoreDi }).name, "B_mm"); // m vs mm: no value guard
  assert.equal(campoPerTesto("H = 2,70 m", FIELDS, { campo: "b", valoreDi }).name, "b"); // a computed total edits its input
  assert.equal(campoPerTesto("B = 1,50 m", FIELDS, { campo: "zona", valoreDi }), null); // not a number field
  assert.equal(campoPerTesto("B = 1,50 m", FIELDS, { campo: "nope", valoreDi }), null);
});
