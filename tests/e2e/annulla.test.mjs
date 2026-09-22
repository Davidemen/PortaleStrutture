// Pure undo/redo stack (js/annulla.js, WORKBENCH_SPEC §21): registering a step, undoing/redoing,
// the 100-step limit, redo cleared by a new edit, and every returned object a NEW instance (never
// the input storia/its arrays -- the immutability the app itself relies on to detect "did the
// values actually change" without a deep-diff of the caller's own object).
import test from "node:test";
import assert from "node:assert/strict";
import { creaStoria, registra, annulla, ripristina, puoAnnullare, puoRipristinare, passoAnnulla, passoRipristina, MAX_PASSI_ANNULLA } from "../../src/strutture/web/static/js/annulla.js";

function passo(etichetta, valori, campo = null) {
  return { etichetta, testo: etichetta, campo, valori };
}

test("a fresh history has nothing to undo or redo", () => {
  const storia = creaStoria({ a: 1 });
  assert.equal(puoAnnullare(storia), false);
  assert.equal(puoRipristinare(storia), false);
  assert.deepEqual(storia.presente, { a: 1 });
});

test("registra pushes the OLD presente as the restorable step and adopts the new values", () => {
  const s0 = creaStoria({ a: 1 });
  const s1 = registra(s0, passo("a: 1 → 2", { a: 2 }, "a"));
  assert.equal(puoAnnullare(s1), true);
  assert.deepEqual(s1.presente, { a: 2 });
  assert.deepEqual(passoAnnulla(s1), { etichetta: "a: 1 → 2", testo: "a: 1 → 2", campo: "a", valori: { a: 1 } });
});

test("annulla restores the previous values and moves the step to futuro", () => {
  const s0 = creaStoria({ a: 1 });
  const s1 = registra(s0, passo("a: 1 → 2", { a: 2 }));
  const s2 = annulla(s1);
  assert.deepEqual(s2.presente, { a: 1 });
  assert.equal(puoAnnullare(s2), false);
  assert.equal(puoRipristinare(s2), true);
  assert.deepEqual(passoRipristina(s2).valori, { a: 2 });
});

test("ripristina re-applies an undone step", () => {
  const s0 = creaStoria({ a: 1 });
  const s2 = annulla(registra(s0, passo("a: 1 → 2", { a: 2 })));
  const s3 = ripristina(s2);
  assert.deepEqual(s3.presente, { a: 2 });
  assert.equal(puoRipristinare(s3), false);
});

test("a new registered step after an undo clears the redo branch", () => {
  const s0 = creaStoria({ a: 1 });
  const s2 = annulla(registra(s0, passo("a: 1 → 2", { a: 2 })));
  const s3 = registra(s2, passo("a: 1 → 5", { a: 5 }));
  assert.equal(puoRipristinare(s3), false);
  assert.deepEqual(s3.presente, { a: 5 });
});

test("annulla/ripristina on an empty stack are no-ops", () => {
  const storia = creaStoria({ a: 1 });
  assert.equal(annulla(storia), storia);
  assert.equal(ripristina(storia), storia);
});

test("the oldest step is dropped silently past MAX_PASSI_ANNULLA", () => {
  let storia = creaStoria({ a: 0 });
  for (let i = 1; i <= MAX_PASSI_ANNULLA + 10; i += 1) {
    storia = registra(storia, passo(`a: ${i}`, { a: i }));
  }
  assert.equal(storia.passato.length, MAX_PASSI_ANNULLA);
  assert.deepEqual(storia.passato[0].valori, { a: 10 }); // the first 10 steps were dropped
});

test("every function returns a NEW object, never the same instance as the input", () => {
  const s0 = creaStoria({ a: 1 });
  const s1 = registra(s0, passo("a: 1 → 2", { a: 2 }));
  assert.notEqual(s1, s0);
  assert.notEqual(s1.passato, s0.passato);
  const s2 = annulla(s1);
  assert.notEqual(s2, s1);
  assert.notEqual(s2.futuro, s1.futuro);
  const s3 = ripristina(s2);
  assert.notEqual(s3, s2);
  assert.notEqual(s3.passato, s2.passato);
});
