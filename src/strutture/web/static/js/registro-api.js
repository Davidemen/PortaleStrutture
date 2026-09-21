// Thin fetch wrappers for the divergence register API (WORKBENCH_SPEC §13). Every function
// throws a plain Error with an Italian message on any failure -- network, non-200 status or an
// unparsable body -- so callers can render it inline instead of swallowing it.
async function readJson(response) {
  try {
    return await response.json();
  } catch (error) {
    throw new Error("Risposta del server non valida.");
  }
}

function serverMessage(body, fallback) {
  return (body && Array.isArray(body.errors) && body.errors[0]) || fallback;
}

async function get(url, fallbackMessage) {
  let response;
  try {
    response = await fetch(url);
  } catch (error) {
    throw new Error("Impossibile contattare il server.");
  }
  const body = await readJson(response);
  if (response.status !== 200) throw new Error(serverMessage(body, fallbackMessage));
  return body;
}

async function send(url, method, payload, fallbackMessage) {
  let response;
  try {
    response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    throw new Error("Impossibile contattare il server.");
  }
  const body = await readJson(response);
  if (response.status !== 200) throw new Error(serverMessage(body, fallbackMessage));
  return body;
}

// `{divergenze, totali}` -- `stato` is deliberately never sent here: the register page fetches
// every state that matches strumento/tipo/q ONCE and applies the state filter itself, so the
// totals strip can show all three counts regardless of which one is currently selected.
export function fetchDivergenze({ strumento, tipo, q } = {}) {
  const params = new URLSearchParams();
  if (strumento) params.set("strumento", strumento);
  if (tipo) params.set("tipo", tipo);
  if (q) params.set("q", q);
  const query = params.toString();
  return get(`/api/divergences${query ? `?${query}` : ""}`, "Impossibile caricare il registro delle correzioni.");
}

// Total `da_confermare` count across every tool -- the rail's own pending-count chip (WORKBENCH_SPEC
// §13.1: "a count chip with the number still da_confermare, hidden at 0").
export function fetchTotalePendenti() {
  return fetchDivergenze().then((body) => (body.totali && body.totali.da_confermare) || 0);
}

// `{<tool>: {da_confermare, approvato, respinto}}`.
export function fetchRiepilogo() {
  return get("/api/divergences/riepilogo", "Impossibile caricare il riepilogo delle correzioni.").then(
    (body) => body.per_strumento || {}
  );
}

// One entry (register fields + stato/sigla/nota/data) plus `storia` (every past decision, oldest first).
export function fetchDivergenza(id) {
  const [unita, slug] = String(id).split("/");
  return get(`/api/divergences/${encodeURIComponent(unita)}/${encodeURIComponent(slug)}`, "Correzione non trovata.");
}

export function signoff(id, { stato, sigla, nota }) {
  const [unita, slug] = String(id).split("/");
  return send(
    `/api/divergences/${encodeURIComponent(unita)}/${encodeURIComponent(slug)}/signoff`,
    "PUT",
    { stato, sigla, nota },
    "Impossibile salvare la decisione."
  );
}

export function signoffMultiplo({ ids, stato, sigla, nota }) {
  return send("/api/divergences/signoff-multiplo", "POST", { ids, stato, sigla, nota }, "Impossibile salvare le decisioni.");
}
