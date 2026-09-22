// Thin fetch wrappers for /api/progetti and /api/elementi (docs/architecture-phase3.md,
// src/strutture/web/routes/progetti.py). Same contract as js/registro-api.js: every function
// throws a plain Error with an Italian message on any network/parse/4xx-5xx failure, so callers
// render it inline instead of swallowing it. The one difference is the optimistic-locking 409 a
// PUT/DELETE can return (`_conflict_envelope`, routes/progetti.py): that resolves normally as
// `{conflict: true, attuale, message}` instead of throwing, so js/elemento-salva.js can show the
// "Ricarica / Salva come copia" dialog with the server's current record instead of a bare error.
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

async function request(url, { method = "GET", body, fallback } = {}) {
  // `SameOriginMiddleware` (src/strutture/web/middleware/same_origin.py, CSRF protection) rejects
  // EVERY unsafe method (POST/PUT/PATCH/DELETE) on `/api/*` with 415 unless it declares
  // `Content-Type: application/json` -- unconditionally, even a POST that carries no meaningful
  // body of its own (`restoreProgetto`'s `.../ripristina`, whose route never calls
  // `request.json()` either). The header (and an empty-object body, so a declared JSON content
  // type is never paired with a zero-length one) goes on every non-GET call here, not only when
  // the caller actually passed a `body`.
  const isUnsafe = method !== "GET";
  let response;
  try {
    response = await fetch(url, {
      method,
      headers: isUnsafe ? { "Content-Type": "application/json" } : undefined,
      body: isUnsafe ? JSON.stringify(body ?? {}) : undefined,
    });
  } catch (error) {
    throw new Error("Impossibile contattare il server.");
  }
  const data = await readJson(response);
  if (response.status === 409) return { conflict: true, attuale: data.attuale, message: serverMessage(data, fallback) };
  if (response.status < 200 || response.status >= 300) throw new Error(serverMessage(data, fallback));
  return { conflict: false, data };
}

// -- progetti ------------------------------------------------------------------------------------

export async function fetchProgetti({ inclusiEliminati = false } = {}) {
  const query = inclusiEliminati ? "?inclusi_eliminati=true" : "";
  const { data } = await request(`/api/progetti${query}`, { fallback: "Impossibile caricare l'elenco dei progetti." });
  return data;
}

export async function fetchProgetto(id) {
  const { data } = await request(`/api/progetti/${encodeURIComponent(id)}`, { fallback: "Progetto non trovato." });
  return data;
}

export async function createProgetto({ codice = "", nome, committente = "", note = "" }) {
  const { data } = await request("/api/progetti", {
    method: "POST",
    body: { codice, nome, committente, note },
    fallback: "Impossibile creare il progetto.",
  });
  return data;
}

// Resolves to `{conflict, data}` (or `{conflict: true, attuale, message}`) -- the caller decides
// what a conflicting rename means (routes/progetti.py never resolves it server-side).
export function updateProgetto(id, { codice, nome, committente, note, revisione }) {
  return request(`/api/progetti/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: { codice, nome, committente, note, revisione },
    fallback: "Impossibile salvare il progetto.",
  });
}

export function deleteProgetto(id, revisione) {
  return request(`/api/progetti/${encodeURIComponent(id)}`, {
    method: "DELETE",
    body: { revisione },
    fallback: "Impossibile eliminare il progetto.",
  });
}

export async function restoreProgetto(id) {
  const { data } = await request(`/api/progetti/${encodeURIComponent(id)}/ripristina`, {
    method: "POST",
    fallback: "Impossibile ripristinare il progetto.",
  });
  return data;
}

// -- elementi --------------------------------------------------------------------------------------

export async function fetchElementi(progettoId, { inclusiEliminati = false } = {}) {
  const query = inclusiEliminati ? "?inclusi_eliminati=true" : "";
  const { data } = await request(`/api/progetti/${encodeURIComponent(progettoId)}/elementi${query}`, {
    fallback: "Impossibile caricare gli elementi del progetto.",
  });
  return data;
}

export async function createElemento(progettoId, body) {
  const { data } = await request(`/api/progetti/${encodeURIComponent(progettoId)}/elementi`, {
    method: "POST",
    body,
    fallback: "Impossibile salvare l'elemento.",
  });
  return data;
}

export async function fetchElemento(id) {
  const { data } = await request(`/api/elementi/${encodeURIComponent(id)}`, { fallback: "Elemento non trovato." });
  return data;
}

export function updateElemento(id, body) {
  return request(`/api/elementi/${encodeURIComponent(id)}`, { method: "PUT", body, fallback: "Impossibile salvare l'elemento." });
}

export function deleteElemento(id, revisione) {
  return request(`/api/elementi/${encodeURIComponent(id)}`, {
    method: "DELETE",
    body: { revisione },
    fallback: "Impossibile eliminare l'elemento.",
  });
}

export async function restoreElemento(id) {
  const { data } = await request(`/api/elementi/${encodeURIComponent(id)}/ripristina`, {
    method: "POST",
    fallback: "Impossibile ripristinare l'elemento.",
  });
  return data;
}

export async function duplicateElemento(id, nome) {
  const { data } = await request(`/api/elementi/${encodeURIComponent(id)}/duplica`, {
    method: "POST",
    body: { nome },
    fallback: "Impossibile duplicare l'elemento.",
  });
  return data;
}

export async function fetchRevisioni(id) {
  const { data } = await request(`/api/elementi/${encodeURIComponent(id)}/revisioni`, {
    fallback: "Impossibile caricare la storia dell'elemento.",
  });
  return data;
}

// -- export / import ------------------------------------------------------------------------------

export async function fetchExportPayload(progettoId) {
  const { data } = await request(`/api/progetti/${encodeURIComponent(progettoId)}/esporta`, {
    fallback: "Impossibile esportare il progetto.",
  });
  return data;
}

// `{progetto, avvisi}` -- `avvisi` includes one Italian sentence per element with an unknown tool.
export async function importProgetto(payload) {
  const { data } = await request("/api/progetti/importa", {
    method: "POST",
    body: payload,
    fallback: "Impossibile importare il progetto.",
  });
  return data;
}
