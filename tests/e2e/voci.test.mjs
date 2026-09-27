// Pure logic of the "voce unica" screen (WORKBENCH_SPEC §27): the entry table (js/voci.js) and
// the common-data rules (js/voce-comuni.js). The DOM side is covered by tests/e2e/test_voce_*.py.
import test from "node:test";
import assert from "node:assert/strict";
import {
  VOCI,
  voceDiStrumento,
  voceDaSlug,
  indirizzoVoce,
  rappresentante,
  elencoConVoci,
  nomiUnici,
  parteOpzionale,
} from "../../src/strutture/web/static/js/voci.js";
import {
  propaga,
  stacca,
  ricollega,
  condiviso,
  campiCompagno,
  prefissaCampi,
  senzaPrefisso,
  valoreDaRicollegare,
} from "../../src/strutture/web/static/js/voce-comuni.js";

const neve = voceDaSlug("carichi/neve");

test("§27.8: the common data of Neve are exactly the five the owner fixed (not `a`)", () => {
  assert.deepEqual(neve.comuni, ["comune", "zona", "as_m", "ct", "topografia"]);
  assert.equal(neve.predefinita, "neve-carico-falda");
  assert.deepEqual(neve.parti.map((p) => p.tool), ["neve-carico-falda", "neve-accumulo"]);
  assert.equal(parteOpzionale(neve).tool, "neve-accumulo");
  assert.equal(parteOpzionale(neve).casella, "Accumulo");
});

test("every entry has a unique slug and every tool belongs to one entry at most", () => {
  const slugs = VOCI.map((v) => v.slug);
  assert.equal(new Set(slugs).size, slugs.length);
  const tools = VOCI.flatMap((v) => v.parti.map((p) => p.tool));
  assert.equal(new Set(tools).size, tools.length);
});

test("voceDiStrumento / rappresentante map a part to its entry and default part", () => {
  assert.equal(voceDiStrumento("neve-accumulo"), neve);
  assert.equal(voceDiStrumento("muro-sostegno"), null);
  assert.equal(rappresentante("neve-accumulo"), "neve-carico-falda");
  assert.equal(rappresentante("muro-sostegno"), "muro-sostegno");
});

test("indirizzoVoce keeps every query parameter and puts parte first", () => {
  assert.deepEqual(indirizzoVoce(neve, "neve-accumulo", { as_m: "333", elemento: "e1" }), {
    path: "voce/carichi/neve",
    params: { parte: "neve-accumulo", as_m: "333", elemento: "e1" },
  });
});

const TOOLS = [
  { name: "vento-pressione", title: "Pressione del vento", group: "Carichi / Vento", sigla: "VP" },
  { name: "neve-carico-falda", title: "Carico neve su copertura", group: "Carichi / Neve", sigla: "NC", norm: "NTC", summary: "s1" },
  { name: "neve-accumulo", title: "Accumulo neve", group: "Carichi / Neve", sigla: "NA", summary: "s2" },
  { name: "muro-sostegno", title: "Muro", group: "Geotecnica / Muri", sigla: "MU" },
];

test("elencoConVoci lists the entry once, where its first part was, under the default part's name", () => {
  const list = elencoConVoci(TOOLS);
  assert.deepEqual(list.map((t) => t.name), ["vento-pressione", "neve-carico-falda", "muro-sostegno"]);
  const voce = list[1];
  assert.equal(voce.title, "Neve");
  assert.equal(voce.sigla, "NC");
  assert.equal(voce.norm, "NTC");
  assert.equal(voce.group, "Carichi / Neve");
  assert.match(voce.cerca, /Accumulo neve/);
  assert.match(voce.cerca, /Carico neve su copertura/);
});

test("nomiUnici de-duplicates favourites/recents per entry, keeping the order", () => {
  assert.deepEqual(nomiUnici(["neve-accumulo", "muro-sostegno", "neve-carico-falda"]), ["neve-carico-falda", "muro-sostegno"]);
});

test("propaga writes attached common fields into the other parts, never a detached one", () => {
  const valoriDi = { "neve-accumulo": { as_m: 249, comune: "Bergamo", a: 5 } };
  const out = propaga(neve, "neve-carico-falda", { as_m: 612, comune: "Mapello", a: 0, ct: 1 }, {}, valoriDi);
  assert.deepEqual(out, { "neve-accumulo": { as_m: 612, comune: "Mapello", a: 5, ct: 1 } });
  const staccati = stacca({}, "neve-carico-falda", "as_m");
  const out2 = propaga(neve, "neve-carico-falda", { as_m: 700, comune: "Mapello" }, staccati, valoriDi);
  assert.deepEqual(out2, { "neve-accumulo": { as_m: 249, comune: "Mapello", a: 5 } });
});

test("propaga returns nothing when no other part changes", () => {
  const valoriDi = { "neve-accumulo": { as_m: 612 } };
  assert.deepEqual(propaga(neve, "neve-carico-falda", { as_m: 612 }, {}, valoriDi), {});
});

test("stacca/ricollega/condiviso are immutable and symmetric between the two parts", () => {
  const s0 = {};
  const s1 = stacca(s0, "neve-accumulo", "ct");
  assert.deepEqual(s0, {});
  assert.equal(condiviso(neve, s1, "ct"), false);
  assert.equal(condiviso(neve, s1, "as_m"), true);
  const s2 = ricollega(s1, "ct");
  assert.equal(condiviso(neve, s2, "ct"), true);
  assert.deepEqual(s2, {});
});

test("valoreDaRicollegare takes the value of the other part", () => {
  const valoriDi = { "neve-carico-falda": { as_m: 250 }, "neve-accumulo": { as_m: 700 } };
  assert.equal(valoreDaRicollegare(neve, "neve-carico-falda", "as_m", valoriDi), 700);
});

test("campiCompagno hides shared common fields and shows detached ones", () => {
  const fields = [{ name: "comune" }, { name: "as_m" }, { name: "h" }, { name: "a" }];
  assert.deepEqual(campiCompagno(neve, fields, {}).map((f) => f.name), ["h", "a"]);
  const staccati = stacca({}, "neve-carico-falda", "as_m");
  assert.deepEqual(campiCompagno(neve, fields, staccati).map((f) => f.name), ["as_m", "h", "a"]);
});

test("prefissaCampi renames fields and their conditions; senzaPrefisso strips it back", () => {
  const fields = [{ name: "tipo" }, { name: "a", condition: { field: "tipo", equals: "x" } }];
  const out = prefissaCampi(fields, "cmp__");
  assert.deepEqual(out.map((f) => f.name), ["cmp__tipo", "cmp__a"]);
  assert.deepEqual(out[1].condition, { field: "cmp__tipo", equals: "x" });
  assert.deepEqual(fields[1].condition, { field: "tipo", equals: "x" });
  assert.deepEqual(senzaPrefisso({ cmp__tipo: "x", cmp__a: 2 }, "cmp__"), { tipo: "x", a: 2 });
});
