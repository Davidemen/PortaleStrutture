// Pure-function unit tests for js/impostazioni-modello.js (WORKBENCH_SPEC §26.8): dirty
// detection, the readable diff and duplicate-exception detection. No DOM, no server:
//   node --test tests/e2e/impostazioni.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { FACTORY, cloneState, isDirty, eccezioniDuplicate, diffLeggibile, campiPerStrumento } from "../../src/strutture/web/static/js/impostazioni-modello.js";

test("cloneState never returns the same array/object references (immutability)", () => {
  const original = { obiettivo_sfruttamento: 1, obiettivo_su_verifiche_minimo: false, passi_per_tipo: { spessore: 5 }, passi_per_campo: [{ strumento: "a", campo: "b", passo: 1 }] };
  const clone = cloneState(original);
  assert.deepEqual(clone, original);
  assert.notEqual(clone.passi_per_tipo, original.passi_per_tipo);
  assert.notEqual(clone.passi_per_campo, original.passi_per_campo);
  assert.notEqual(clone.passi_per_campo[0], original.passi_per_campo[0]);
});

test("isDirty compares by value, not by reference", () => {
  const a = cloneState(FACTORY);
  const b = cloneState(FACTORY);
  assert.equal(isDirty(a, b), false);
  b.obiettivo_sfruttamento = 0.9;
  assert.equal(isDirty(a, b), true);
});

test("eccezioniDuplicate flags the SECOND occurrence of a (strumento, campo) pair", () => {
  const passi = [
    { strumento: "muro-sostegno", campo: "h_mm", passo: 10 },
    { strumento: "muro-sostegno", campo: "b_mm", passo: 10 },
    { strumento: "muro-sostegno", campo: "h_mm", passo: 20 },
  ];
  assert.deepEqual([...eccezioniDuplicate(passi)], [2]);
});

test("diffLeggibile reports the obiettivo, a type step and an added exception", () => {
  const prima = cloneState(FACTORY);
  const dopo = { ...cloneState(FACTORY), obiettivo_sfruttamento: 0.9, passi_per_tipo: { diametro_armatura: 2 }, passi_per_campo: [{ strumento: "a", campo: "b", passo: 5 }] };
  const righe = diffLeggibile(prima, dopo);
  assert.ok(righe.some((r) => r.startsWith("Obiettivo 1")));
  assert.ok(righe.some((r) => r.includes("diametro_armatura")));
  assert.ok(righe.some((r) => r.startsWith("Eccezione aggiunta: a.b")));
});

test("diffLeggibile reports nothing for two identical states", () => {
  assert.deepEqual(diffLeggibile(cloneState(FACTORY), cloneState(FACTORY)), []);
});

test("campiPerStrumento groups both typed and untyped fields by tool", () => {
  const tipi = {
    tipi: [{ tipo: "spessore", campi: [{ strumento: "a", campo: "s_mm", simbolo: "t", etichetta: "Spessore", unita: "mm" }] }],
    senza_tipo: [{ strumento: "a", campo: "alfa", simbolo: "α", etichetta: "Angolo", unita: "°" }],
  };
  const map = campiPerStrumento(tipi);
  assert.deepEqual(map.get("a").map((c) => c.campo), ["s_mm", "alfa"]);
});
