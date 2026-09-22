// Pure state transitions for "Varianti affiancate" (js/varianti-state.js, WORKBENCH_SPEC §19.1/
// §19.2): no DOM/storage touched by any of these -- `caricaVarianti`/`salvaVarianti`/
// `chiudiVarianti` (the only functions that DO touch `sessionStorage`) are exercised by the e2e
// suite (tests/e2e/test_varianti.py) instead, same split as js/varianti-diff.js's own tests.
import test from "node:test";
import assert from "node:assert/strict";
import {
  MAX_VARIANTI,
  iniziaVarianti,
  aggiungiVariante,
  duplicaVariante,
  attivaVariante,
  rinominaVariante,
  eliminaVariante,
  aggiornaInputsVariante,
  puoAggiungere,
  trovaVariante,
  varianteAttiva,
  etichettaTab,
} from "../../src/strutture/web/static/js/varianti-state.js";

test("iniziaVarianti clones the current inputs into A and B, B active, A carries origine", () => {
  const origine = { elemento_id: "e1", revisione: 3, nome: "Sito" };
  const set = iniziaVarianti({ x: 1 }, origine);
  assert.equal(set.attiva, "B");
  assert.deepEqual(set.varianti.map((v) => v.id), ["A", "B"]);
  assert.deepEqual(set.varianti[0].inputs, { x: 1 });
  assert.deepEqual(set.varianti[1].inputs, { x: 1 });
  assert.equal(set.varianti[0].origine, origine);
  assert.equal(set.varianti[1].origine, null);
  // Cloned, not shared -- mutating the ORIGINAL object afterwards must never leak into a variant.
  const inputsCorrenti = { x: 1 };
  const set2 = iniziaVarianti(inputsCorrenti, null);
  inputsCorrenti.x = 99;
  assert.equal(set2.varianti[0].inputs.x, 1);
});

test("aggiungiVariante copies the ACTIVE variant into the next free letter and activates it", () => {
  let set = iniziaVarianti({ x: 1 }, null);
  set = attivaVariante(set, "A");
  set = aggiungiVariante(set); // copies A -> C (B already taken), C active
  assert.equal(set.attiva, "C");
  assert.deepEqual(set.varianti.map((v) => v.id), ["A", "B", "C"]);
  assert.deepEqual(trovaVariante(set, "C").inputs, { x: 1 });
});

test("aggiungiVariante/duplicaVariante refuse past MAX_VARIANTI", () => {
  let set = iniziaVarianti({}, null);
  while (puoAggiungere(set)) set = aggiungiVariante(set);
  assert.equal(set.varianti.length, MAX_VARIANTI);
  const stesso = aggiungiVariante(set);
  assert.equal(stesso, set); // no-op, never throws, never exceeds the cap
  assert.equal(duplicaVariante(set, "A"), set);
});

test("duplicaVariante copies a SPECIFIC (not necessarily active) variant", () => {
  let set = iniziaVarianti({ x: 1 }, null);
  set = { ...set, varianti: set.varianti.map((v) => (v.id === "A" ? { ...v, inputs: { x: 42 } } : v)) };
  set = duplicaVariante(set, "A"); // duplicates A (inactive), not B (active)
  const nuova = trovaVariante(set, set.attiva);
  assert.deepEqual(nuova.inputs, { x: 42 });
});

test("eliminaVariante refuses to drop the last variant and reassigns `attiva` when needed", () => {
  let set = iniziaVarianti({}, null);
  assert.equal(eliminaVariante({ attiva: "A", varianti: [{ id: "A", nome: "A", inputs: {} }] }, "A").varianti.length, 1);
  set = eliminaVariante(set, "B"); // B was active
  assert.equal(set.attiva, "A"); // falls back to the first remaining
  assert.equal(set.varianti.length, 1);
});

test("rinominaVariante trims/caps the name and falls back to the id when blank", () => {
  let set = iniziaVarianti({}, null);
  set = rinominaVariante(set, "A", "  Caso base  ");
  assert.equal(trovaVariante(set, "A").nome, "Caso base");
  set = rinominaVariante(set, "A", "   ");
  assert.equal(trovaVariante(set, "A").nome, "A");
});

test("aggiornaInputsVariante replaces only the named variant's inputs", () => {
  let set = iniziaVarianti({ x: 1 }, null);
  set = aggiornaInputsVariante(set, "B", { x: 2 });
  assert.deepEqual(trovaVariante(set, "A").inputs, { x: 1 });
  assert.deepEqual(trovaVariante(set, "B").inputs, { x: 2 });
});

test("varianteAttiva/trovaVariante tolerate a null set", () => {
  assert.equal(varianteAttiva(null), null);
  assert.equal(trovaVariante(null, "A"), null);
});

test("etichettaTab shows the id alone once, id + nome when renamed", () => {
  let set = iniziaVarianti({}, null);
  assert.equal(etichettaTab(trovaVariante(set, "A")), "A");
  set = rinominaVariante(set, "A", "Caso base");
  assert.equal(etichettaTab(trovaVariante(set, "A")), "A · Caso base");
});
