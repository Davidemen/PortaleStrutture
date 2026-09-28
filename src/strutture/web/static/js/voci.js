// "Voce unica" entry table -- WORKBENCH_SPEC §27.2/§27.8. Pure data + pure helpers, no DOM: the
// composition of each entry encodes the owner's choices (issue #7), so it is UI data kept here,
// never derived from the schema. An entry groups existing tools; every part still runs through
// its own `POST /api/tools/<name>/run` exactly as the single-tool page did (§27.1).
//
// Part shape: `{ tool, titolo, casella? }` -- `casella` marks the optional part (Neve, Vento): the
// label of the checkbox that opens its data. `comuni` is the explicit list of §27.4 (same name AND
// same meaning, confirmed by the owner), never "every field with the same name".
export const VOCI = [
  {
    categoria: "Carichi",
    nome: "Neve",
    slug: "carichi/neve",
    parti: [
      { tool: "neve-carico-falda", titolo: "Copertura" },
      { tool: "neve-accumulo", titolo: "Accumulo", casella: "Accumulo" },
    ],
    predefinita: "neve-carico-falda",
    descrizione: "Carico neve sulla copertura; con la casella Accumulo anche l'accumulo a ridosso di costruzioni più alte.",
    // `a` is NOT common: roof pitch in neve-carico-falda, pitch of the taller building in
    // neve-accumulo (owner, issue #7 comment of 2026-09-27).
    comuni: ["comune", "zona", "as_m", "ct", "topografia"],
  },
  {
    categoria: "Carichi",
    nome: "Vento",
    slug: "carichi/vento",
    parti: [
      { tool: "vento-pressione", titolo: "Pressione" },
      { tool: "vento-cpe-rettangolare", titolo: "Coefficienti Cpe", casella: "Coefficienti Cpe" },
    ],
    predefinita: "vento-pressione",
    descrizione: "Pressione cinetica e profilo lungo l'altezza; con la casella Coefficienti Cpe anche i coefficienti di pressione esterna di un edificio rettangolare.",
    // §27.8: no field with the same name and meaning. H (pressione) vs h (Cpe) is an open
    // engineering question for the owner (issue #17): separate until decided.
    comuni: [],
  },
];

const PER_STRUMENTO = new Map(VOCI.flatMap((voce) => voce.parti.map((parte) => [parte.tool, voce])));

export function voceDiStrumento(name) {
  return PER_STRUMENTO.get(name) || null;
}

export function voceDaSlug(slug) {
  return VOCI.find((voce) => voce.slug === slug) || null;
}

export function parteOpzionale(voce) {
  return voce.parti.find((parte) => parte.casella) || null;
}

export function parteDi(voce, tool) {
  return voce.parti.find((parte) => parte.tool === tool) || null;
}

// §27.5: `#/voce/<category-slug>/<entry-slug>?parte=<tool>&<field>=<value>&…`.
export function indirizzoVoce(voce, parte, params = {}) {
  const { parte: _ignorata, ...resto } = params;
  return { path: `voce/${voce.slug}`, params: { parte, ...resto } };
}

// The tool name the rail, Home and the palette use for the entry's one row.
export function rappresentante(name) {
  const voce = voceDiStrumento(name);
  return voce ? voce.predefinita : name;
}

// §27.5: rail, flyouts, Home and the palette list the entry once (title = entry name, sigla and
// norm of the default part), placed where its first part was. `cerca` carries the parts' titles
// so the palette/Home search still finds the entry by them.
export function elencoConVoci(tools) {
  const result = [];
  const fatte = new Set();
  for (const tool of tools) {
    const voce = voceDiStrumento(tool.name);
    if (!voce) {
      result.push(tool);
      continue;
    }
    if (fatte.has(voce.slug)) continue;
    fatte.add(voce.slug);
    const parti = voce.parti.map((parte) => tools.find((t) => t.name === parte.tool)).filter(Boolean);
    const base = parti.find((t) => t.name === voce.predefinita) || parti[0];
    result.push({
      ...base,
      title: voce.nome,
      summary: voce.descrizione,
      cerca: parti.map((t) => t.title).join(" "),
      voce: voce.slug,
    });
  }
  return result;
}

// Favourites/recents stay stored per tool (§27.5) and are shown de-duplicated per entry.
export function nomiUnici(names) {
  return [...new Set(names.map(rappresentante))];
}
