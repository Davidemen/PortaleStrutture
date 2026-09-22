// Thin fetch wrappers for `/api/impostazioni*` (WORKBENCH_SPEC §26.7/§26.9). `leggiImpostazioni`
// and `leggiTipi` are cached per page load, like js/usa-in.js's `ensureCollegamenti` and
// js/registro-stato.js's own riepilogo cache -- both caches are dropped on `impostazioni:salvate`
// (dispatched on `document` by js/impostazioni.js after a successful save), so §23/§24's dialogs
// never read a stale office default after the settings page just changed it.
async function readJson(response) {
  try {
    return await response.json();
  } catch (error) {
    return { ok: false, errors: ["Risposta del server non valida."] };
  }
}

function serverMessage(body, fallback) {
  return (body && Array.isArray(body.errors) && body.errors[0]) || fallback;
}

let impostazioniCache = null;
let impostazioniPending = null;
let tipiCache = null;
let tipiPending = null;
const passiCache = new Map();

function dropCaches() {
  impostazioniCache = null;
  impostazioniPending = null;
  tipiCache = null;
  tipiPending = null;
  passiCache.clear();
}

document.addEventListener("impostazioni:salvate", dropCaches);

export function leggiImpostazioni() {
  if (impostazioniCache) return Promise.resolve(impostazioniCache);
  if (impostazioniPending) return impostazioniPending;
  impostazioniPending = fetch("/api/impostazioni")
    .then((response) => readJson(response))
    .then((body) => {
      impostazioniCache = body;
      impostazioniPending = null;
      return body;
    })
    .catch(() => {
      impostazioniPending = null;
      throw new Error("Impossibile contattare il server.");
    });
  return impostazioniPending;
}

export async function salvaImpostazioni(payload) {
  let response;
  try {
    response = await fetch("/api/impostazioni", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    return { status: 0, ok: false, body: { errors: ["Impossibile contattare il server."] } };
  }
  const body = await readJson(response);
  if (response.status === 200) {
    impostazioniCache = body;
    dropCaches();
    impostazioniCache = body;
    document.dispatchEvent(new CustomEvent("impostazioni:salvate", { detail: body }));
  }
  return { status: response.status, ok: response.status === 200, body };
}

export function leggiTipi() {
  if (tipiCache) return Promise.resolve(tipiCache);
  if (tipiPending) return tipiPending;
  tipiPending = fetch("/api/impostazioni/tipi")
    .then((response) => readJson(response))
    .then((body) => {
      tipiCache = body;
      tipiPending = null;
      return body;
    })
    .catch(() => {
      tipiPending = null;
      throw new Error("Impossibile contattare il server.");
    });
  return tipiPending;
}

// Cached per tool name, until the settings change: §23.5/§24.2 open a dialog often while
// exploring a tool, and re-fetching the same resolution on every keystroke would be wasteful.
export function passiStrumento(toolName) {
  if (passiCache.has(toolName)) return passiCache.get(toolName);
  const promise = fetch(`/api/impostazioni/passi?strumento=${encodeURIComponent(toolName)}`)
    .then((response) => readJson(response))
    .catch(() => {
      throw new Error("Impossibile contattare il server.");
    });
  passiCache.set(toolName, promise);
  return promise;
}

export async function leggiStoria(limite = 50) {
  let response;
  try {
    response = await fetch(`/api/impostazioni/storia?limite=${limite}`);
  } catch (error) {
    throw new Error("Impossibile contattare il server.");
  }
  const body = await readJson(response);
  if (response.status !== 200) throw new Error(serverMessage(body, "Impossibile caricare la storia."));
  return body;
}
