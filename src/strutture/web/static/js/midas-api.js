// Fetch wrappers for /api/midas/* (MIDAS.md §4 -- the contract this module codes against).
// The key is sent as the `X-Midas-Key` header ONLY when the caller passes a non-empty one
// (MIDAS.md §2 rule 2); it is never put in a query string, never logged, and every failure
// (network, bad JSON, HTTP error, `{ok:false}` body) returns a plain object -- nothing is ever
// thrown, so a caller never needs try/catch and nothing reaches the console.

const GENERIC_ERROR = "Impossibile contattare il server.";
const BAD_RESPONSE_ERROR = "Risposta del server non valida.";

async function call(path, { method = "GET", body, key } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (key) headers["X-Midas-Key"] = key;

  let response;
  try {
    response = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch (error) {
    return { ok: false, errors: [GENERIC_ERROR], kind: "network" };
  }

  let payload;
  try {
    payload = await response.json();
  } catch (error) {
    return { ok: false, errors: [BAD_RESPONSE_ERROR], kind: "bad_response" };
  }

  if (!response.ok || payload.ok === false) {
    const errors = Array.isArray(payload.errors) && payload.errors.length > 0 ? payload.errors : [BAD_RESPONSE_ERROR];
    return { ok: false, errors, kind: payload.kind || "bad_response" };
  }
  return { ok: true, ...payload };
}

// `{server_key, base_url, product}` -- no key header: this only asks whether the SERVER has one.
export function fetchMidasStatus() {
  return call("/api/midas/status");
}

// `{ok, product, name, version, base_url, units}` on success.
export function verifyMidasConnection({ baseUrl, product, key } = {}) {
  return call("/api/midas/verify", { method: "POST", body: { base_url: baseUrl || undefined, product: product || undefined }, key });
}

// `{combinations: [{name, table_name, classification, active, description, famiglia_suggerita}]}`.
export function fetchMidasCombinations({ baseUrl, key } = {}) {
  return call("/api/midas/combinations", { method: "POST", body: { base_url: baseUrl || undefined }, key });
}

// `{supports: [{nodo, x_m, y_m, z_m}]}`.
export function fetchMidasSupports({ baseUrl, key } = {}) {
  return call("/api/midas/supports", { method: "POST", body: { base_url: baseUrl || undefined }, key });
}

// `{righe, n_righe, avvisi}`. Exactly one of `nodi`/`gruppo` is meaningful; omit the other.
export function fetchMidasReactions({ baseUrl, nodi, gruppo, combinazioni, key } = {}) {
  const body = { base_url: baseUrl || undefined, combinazioni };
  if (nodi && nodi.length > 0) body.nodi = nodi;
  if (gruppo) body.gruppo = gruppo;
  return call("/api/midas/reactions", { method: "POST", body, key });
}
