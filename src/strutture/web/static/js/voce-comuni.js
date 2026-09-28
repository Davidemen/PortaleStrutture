// Common data of an entry -- WORKBENCH_SPEC §27.4. Pure: no DOM, no storage (js/voce.js owns
// both). `staccati` = `{ <tool>: [<field>, …] }`, the fields a part has detached ("Stacca"); a
// common field is shared between parts only while no part has detached it. Every function returns
// new objects, never mutating its arguments.

export function eStaccato(staccati, tool, campo) {
  return (staccati[tool] || []).includes(campo);
}

export function condiviso(voce, staccati, campo) {
  return voce.comuni.includes(campo) && voce.parti.every((parte) => !eStaccato(staccati, parte.tool, campo));
}

export function stacca(staccati, tool, campo) {
  if (eStaccato(staccati, tool, campo)) return staccati;
  return { ...staccati, [tool]: [...(staccati[tool] || []), campo] };
}

// "Ricollega" re-attaches the field in every part (with two parts, detaching is symmetric).
export function ricollega(staccati, campo) {
  const result = {};
  for (const [tool, campi] of Object.entries(staccati)) {
    const rimasti = campi.filter((nome) => nome !== campo);
    if (rimasti.length > 0) result[tool] = rimasti;
  }
  return result;
}

// The entry's value a re-attached field takes in `tool`: the one of the first other part.
export function valoreDaRicollegare(voce, tool, campo, valoriDi) {
  const altra = voce.parti.find((parte) => parte.tool !== tool && valoriDi[parte.tool] && campo in valoriDi[parte.tool]);
  return altra ? valoriDi[altra.tool][campo] : undefined;
}

// `valori` just edited in part `daTool` -> for every other part whose shared common fields differ,
// its new full values (`valoriDi[tool]` merged). Parts that would not change are left out.
export function propaga(voce, daTool, valori, staccati, valoriDi) {
  const result = {};
  for (const parte of voce.parti) {
    if (parte.tool === daTool) continue;
    const attuali = valoriDi[parte.tool] || {};
    let nuovi = attuali;
    for (const campo of voce.comuni) {
      if (!(campo in valori) || !condiviso(voce, staccati, campo)) continue;
      if (attuali[campo] === valori[campo]) continue;
      nuovi = { ...nuovi, [campo]: valori[campo] };
    }
    if (nuovi !== attuali) result[parte.tool] = nuovi;
  }
  return result;
}

// The optional part's own sections (§27.3): shared common fields are not repeated there.
export function campiCompagno(voce, fields, staccati) {
  return fields.filter((field) => !condiviso(voce, staccati, field.name));
}

// The optional part's form lives in the same document as the main form: its field names are
// prefixed so `field-<name>` ids and conditions never collide with the main tool's (`a` exists in
// both Neve tools). The prefix is stripped again before the run.
export function prefissaCampi(fields, prefisso) {
  return fields.map((field) => ({
    ...field,
    name: `${prefisso}${field.name}`,
    ...(field.condition ? { condition: { ...field.condition, field: `${prefisso}${field.condition.field}` } } : {}),
  }));
}

export function senzaPrefisso(values, prefisso) {
  return Object.fromEntries(Object.entries(values).map(([name, value]) => [name.startsWith(prefisso) ? name.slice(prefisso.length) : name, value]));
}
