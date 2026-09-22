// Pure diff helpers (js/varianti-diff.js, WORKBENCH_SPEC §19.3): input differences (scalars and
// tables), relative deltas against a reference value, and the union of check names across
// variants. No DOM -- plain `node --test`.
import test from "node:test";
import assert from "node:assert/strict";
import {
  sameValue,
  diffRighe,
  differenzeCampi,
  contaDatiDiversi,
  unioneVerifiche,
  checkPer,
  deltaRelativo,
} from "../../src/strutture/web/static/js/varianti-diff.js";

test("sameValue compares scalars and arrays structurally", () => {
  assert.equal(sameValue(1, 1), true);
  assert.equal(sameValue(1, 2), false);
  assert.equal(sameValue([1, 2], [1, 2]), true);
  assert.equal(sameValue([{ a: 1 }], [{ a: 1 }]), true);
  assert.equal(sameValue([{ a: 1 }], [{ a: 2 }]), false);
});

test("diffRighe counts row-position differences and the larger row count", () => {
  const a = [{ x: 1 }, { x: 2 }];
  const b = [{ x: 1 }, { x: 9 }, { x: 3 }];
  assert.deepEqual(diffRighe(a, b), { diverse: 2, totale: 3 });
  assert.deepEqual(diffRighe(a, a), { diverse: 0, totale: 2 });
});

test("differenzeCampi flags only fields where at least one variant disagrees with the first", () => {
  const fields = [
    { name: "h", kind: "number" },
    { name: "b", kind: "number" },
    { name: "note", kind: "text" },
  ];
  const varianti = [
    { id: "A", inputs: { h: 2, b: 1, note: "x" } },
    { id: "B", inputs: { h: 3, b: 1, note: "x" } },
    { id: "C", inputs: { h: 2, b: 1, note: "x" } },
  ];
  const differenze = differenzeCampi(fields, varianti);
  assert.equal(differenze.find((v) => v.nome === "h").diverso, true);
  assert.equal(differenze.find((v) => v.nome === "b").diverso, false);
  assert.equal(differenze.find((v) => v.nome === "note").diverso, false);
  assert.deepEqual(contaDatiDiversi(fields, varianti), { diverse: 1, totale: 3 });
});

test("differenzeCampi carries a table row-diff summary for a table field", () => {
  const fields = [{ name: "strati", kind: "table" }];
  const varianti = [
    { id: "A", inputs: { strati: [{ h: 1 }, { h: 2 }] } },
    { id: "B", inputs: { strati: [{ h: 1 }, { h: 9 }, { h: 3 }] } },
  ];
  const differenze = differenzeCampi(fields, varianti);
  assert.equal(differenze[0].diverso, true);
  assert.deepEqual(differenze[0].dettaglio, { diverse: 2, totale: 3 });
});

test("unioneVerifiche orders by the reference column then appends checks unique to later columns", () => {
  const riferimento = { checks: [{ name: "Ribaltamento", passed: true, value: 0.5, limit: 1 }, { name: "Scorrimento", passed: false, value: 1.2, limit: 1 }] };
  const altro = { checks: [{ name: "Scorrimento", passed: true, value: 0.8, limit: 1 }, { name: "Solo qui", passed: true, value: 0.1, limit: 1 }] };
  const nomi = unioneVerifiche([riferimento, altro], 0);
  assert.deepEqual(nomi, ["Scorrimento", "Ribaltamento", "Solo qui"]);
  assert.equal(checkPer(altro, "Scorrimento").passed, true);
  assert.equal(checkPer(altro, "assente"), null);
});

test("deltaRelativo reports a percentage with an arrow, or 'uguale' at displayed precision", () => {
  const up = deltaRelativo(11.25, 10);
  assert.equal(up.simbolo, "▲");
  assert.equal(up.testo, "▲ +12,5 %");

  const down = deltaRelativo(9.7, 10);
  assert.equal(down.simbolo, "▼");
  assert.equal(down.testo, "▼ −3,0 %");

  const equal = deltaRelativo(10.001, 10.0009);
  assert.deepEqual(equal, { simbolo: "=", testo: "= uguale" });

  assert.equal(deltaRelativo(5, 0), null);
  assert.equal(deltaRelativo("x", 10), null);
});
