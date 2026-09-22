// Pure form <-> payload helpers for #/impostazioni (WORKBENCH_SPEC §26.8): no DOM, no fetching --
// `tests/e2e/impostazioni.test.mjs` exercises these directly.
export const FACTORY = { obiettivo_sfruttamento: 1, obiettivo_su_verifiche_minimo: false, passi_per_tipo: {}, passi_per_campo: [] };

export function cloneState(impostazioni) {
  return {
    obiettivo_sfruttamento: impostazioni.obiettivo_sfruttamento,
    obiettivo_su_verifiche_minimo: impostazioni.obiettivo_su_verifiche_minimo,
    passi_per_tipo: { ...(impostazioni.passi_per_tipo || {}) },
    passi_per_campo: (impostazioni.passi_per_campo || []).map((e) => ({ ...e })),
  };
}

export function isDirty(loaded, current) {
  return JSON.stringify(loaded) !== JSON.stringify(current);
}

// Groups every numeric field the `/tipi` endpoint knows about by tool name, so the "Eccezioni per
// campo" rows can offer a Campo select without a second per-tool schema fetch.
export function campiPerStrumento(tipiBody) {
  const map = new Map();
  const push = (voce) => {
    if (!map.has(voce.strumento)) map.set(voce.strumento, []);
    map.get(voce.strumento).push(voce);
  };
  for (const tipo of tipiBody.tipi || []) for (const c of tipo.campi || []) push(c);
  for (const c of tipiBody.senza_tipo || []) push(c);
  return map;
}

// A duplicate (strumento, campo) pair among the exception rows, flagged before Salva (§26.8).
export function eccezioniDuplicate(passiPerCampo) {
  const seen = new Set();
  const dup = new Set();
  passiPerCampo.forEach((e, i) => {
    const key = `${e.strumento}\u0000${e.campo}`;
    if (seen.has(key)) dup.add(i);
    seen.add(key);
  });
  return dup;
}

// A short readable diff between two saved `Impostazioni` (§26.8 "Storia delle modifiche").
export function diffLeggibile(prima, dopo) {
  const righe = [];
  if (prima.obiettivo_sfruttamento !== dopo.obiettivo_sfruttamento) {
    righe.push(`Obiettivo ${fmt(prima.obiettivo_sfruttamento)} → ${fmt(dopo.obiettivo_sfruttamento)}`);
  }
  if (prima.obiettivo_su_verifiche_minimo !== dopo.obiettivo_su_verifiche_minimo) {
    righe.push(`Obiettivo sulle verifiche di minimo: ${prima.obiettivo_su_verifiche_minimo ? "sì" : "no"} → ${dopo.obiettivo_su_verifiche_minimo ? "sì" : "no"}`);
  }
  const tipi = new Set([...Object.keys(prima.passi_per_tipo || {}), ...Object.keys(dopo.passi_per_tipo || {})]);
  for (const tipo of tipi) {
    const a = (prima.passi_per_tipo || {})[tipo] ?? null;
    const b = (dopo.passi_per_tipo || {})[tipo] ?? null;
    if (a !== b) righe.push(`${tipo}: ${a === null ? "—" : fmt(a)} → ${b === null ? "—" : fmt(b)}`);
  }
  const before = new Map((prima.passi_per_campo || []).map((e) => [`${e.strumento}.${e.campo}`, e.passo]));
  const after = new Map((dopo.passi_per_campo || []).map((e) => [`${e.strumento}.${e.campo}`, e.passo]));
  for (const [key, passo] of after) {
    if (!before.has(key)) righe.push(`Eccezione aggiunta: ${key} → ${fmt(passo)}`);
    else if (before.get(key) !== passo) righe.push(`Eccezione ${key}: ${fmt(before.get(key))} → ${fmt(passo)}`);
  }
  for (const key of before.keys()) if (!after.has(key)) righe.push(`Eccezione rimossa: ${key}`);
  return righe;
}

function fmt(value) {
  return value === null || value === undefined ? "—" : String(value).replace(".", ",");
}
