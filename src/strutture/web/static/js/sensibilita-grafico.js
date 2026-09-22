// Pure rows/series/guides mapping for the "Sensibilità" chart (WORKBENCH_SPEC §24.2): no DOM, no
// fetching, so `tests/e2e/sensibilita.test.mjs` can exercise the top-5 selection and guide/domain
// rules directly with plain `node --test`.
export const ETA_MAX_GRAFICO = 3;
export const MAX_SERIE = 5;

// "the 5 most critical checks over the range (failed somewhere first, then by max η)".
// Outcome-only checks (no η at all) never make it here -- they have nothing to plot.
export function selectTopChecks(verifiche, max = MAX_SERIE) {
  const conEta = (verifiche || []).filter((v) => (v.eta || []).some((e) => e !== null && e !== undefined));
  const scored = conEta.map((v) => ({
    v,
    fallita: (v.esito || []).some((e) => e === false),
    etaMax: Math.max(0, ...(v.eta || []).filter((e) => e !== null && e !== undefined)),
  }));
  scored.sort((a, b) => {
    if (a.fallita !== b.fallita) return a.fallita ? -1 : 1;
    return b.etaMax - a.etaMax;
  });
  return scored.slice(0, max).map((s) => s.v);
}

export function buildRows(valori, checks) {
  return (valori || []).map((x, i) => {
    const row = { x };
    checks.forEach((check, ci) => {
      row[`s${ci + 1}`] = check.eta[i] ?? null;
    });
    return row;
  });
}

export function buildSeries(checks) {
  return checks.map((check, i) => ({ key: `s${i + 1}`, label: check.nome, className: `c-series-${i + 1}` }));
}

export function buildGuides(currentValue) {
  return Number.isFinite(currentValue) ? [{ value: currentValue, label: "attuale" }] : [];
}

export function buildHGuides(obiettivo) {
  return Number.isFinite(obiettivo) ? [{ value: obiettivo, label: `obiettivo ${obiettivo}` }] : [];
}
