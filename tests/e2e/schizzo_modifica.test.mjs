// Pure matching of a sketch dimension text to a Dati field (js/schizzo-modifica.js
// `campoPerQuota`): symbol AND unit must match a NUMBER field; the value never matters.
import test from "node:test";
import assert from "node:assert/strict";
import { campoPerQuota } from "../../src/strutture/web/static/js/schizzo-modifica.js";

const FIELDS = [
  { name: "b", kind: "number", symbol: "b", unit: "m" },
  { name: "d", kind: "number", symbol: "d", unit: "m" },
  { name: "B_mm", kind: "number", symbol: "B", unit: "mm" },
  { name: "mu", kind: "number", symbol: "μ", unit: "" },
  { name: "zona", kind: "enum", symbol: "Z", unit: "" },
];

test("matches symbol and unit of a number field, whatever the shown value", () => {
  assert.equal(campoPerQuota("b = 15,00 m", FIELDS).name, "b");
  assert.equal(campoPerQuota("d = 12,00 m", FIELDS).name, "d");
  assert.equal(campoPerQuota("b = 40,00 m", FIELDS).name, "b"); // compressed drawing, true value printed
});

test("a different unit, a non-number field or an unknown symbol give null", () => {
  assert.equal(campoPerQuota("B = 1,50 m", FIELDS), null); // field is in mm, sketch in m
  assert.equal(campoPerQuota("Z = 2", FIELDS), null); // enum
  assert.equal(campoPerQuota("H = 3,00 m", FIELDS), null);
  assert.equal(campoPerQuota("", FIELDS), null);
  assert.equal(campoPerQuota("vento", FIELDS), null);
});

test("a dimensionless field matches a text without unit", () => {
  assert.equal(campoPerQuota("μ = 0,80", FIELDS).name, "mu");
});

test("an explicit `campo` from the sketch wins, but only for an existing number field", () => {
  assert.equal(campoPerQuota("B = 1,50 m", FIELDS, "B_mm").name, "B_mm"); // sketch in m, field in mm
  assert.equal(campoPerQuota("B = 1,50 m", FIELDS, "zona"), null); // not a number field
  assert.equal(campoPerQuota("B = 1,50 m", FIELDS, "nope"), null);
});
