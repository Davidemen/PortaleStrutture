// Pure helpers for the "Dimensiona"/"Sensibilità" dialogs (WORKBENCH_SPEC §23.5/§24.2): the
// numeric-field list a "Campo" select offers, and the Da/A prefill rule -- kept dependency-free
// (no DOM) so `tests/e2e/dimensiona.test.mjs` can exercise them with plain `node --test`.

// A field the dialogs can search on: numeric (kind "number"), not `legacy_compat` (schema.js's
// own describeFields already gives it kind "boolean"), and not advanced-only-hidden -- advanced
// fields ARE offered (the spec only excludes tables/enums/booleans/legacy_compat, §23.4).
export function campiNumerici(fields) {
  return (fields || []).filter((f) => f.kind === "number" && f.name !== "legacy_compat");
}

function proposalHalf(value) {
  return value * 0.5;
}

function proposalDouble(value) {
  return value * 2;
}

// §23.5: "da"/"a" prefill from the field's own schema bounds and its current value. Returns
// `{da, a}` with `null` where the dialog should start empty and required -- including when an
// EXCLUSIVE bound is the only one available and current×0,5 (or ×2) is not strictly past it: a
// server 422 always rejects the bound itself as a `da`/`a`, so proposing it (the previous
// `Math.max(exclusiveMin, proposta)`/`Math.min` rule, which can equal the bound exactly whenever
// the proposed half/double falls short of it) is worse than leaving the field empty and required.
export function prefillRange(field, currentValue) {
  const current = typeof currentValue === "number" && Number.isFinite(currentValue) ? currentValue : null;
  if (current === null || current <= 0) return { da: null, a: null };

  let da = null;
  if (typeof field.minimum === "number") {
    da = field.minimum;
  } else if (typeof field.exclusiveMin === "number") {
    const proposta = proposalHalf(current);
    da = proposta > field.exclusiveMin ? proposta : null;
  } else {
    da = proposalHalf(current);
  }

  let a = null;
  if (typeof field.maximum === "number") {
    a = field.maximum;
  } else if (typeof field.exclusiveMax === "number") {
    const proposta = proposalDouble(current);
    a = proposta < field.exclusiveMax ? proposta : null;
  } else {
    a = proposalDouble(current);
  }

  return { da, a };
}

// The provenance line under "Passo" (§23.1).
export function origineTesto(origine) {
  if (origine === "campo") return "Passo d'ufficio per questo campo";
  if (origine === "tipo") return "Passo d'ufficio per il tipo di dato";
  if (origine === "intero") return "Numero intero";
  return "";
}

export function groupFields(fields) {
  const groups = new Map();
  for (const field of fields) {
    const key = field.group || "Altro";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(field);
  }
  return groups;
}
