// `GET /api/tools/collegamenti` (WORKBENCH_SPEC §15), fetched once and cached -- split out of
// js/usa-in.js so js/provenienza.js (§25.1) can read the same registry without a module cycle
// (usa-in.js reads state from js/elemento-salva.js, which reads js/provenienza.js).
let registry = null; // {chiavi, per_strumento} | null
let pending = null; // in-flight Promise<...> | null -- de-dupes concurrent callers

async function readJson(response) {
  try {
    return await response.json();
  } catch (error) {
    throw new Error("Risposta del server non valida.");
  }
}

async function fetchCollegamentiRaw() {
  let response;
  try {
    response = await fetch("/api/tools/collegamenti");
  } catch (error) {
    throw new Error("Impossibile contattare il server.");
  }
  const body = await readJson(response);
  if (response.status !== 200) {
    throw new Error((body.errors && body.errors[0]) || "Impossibile caricare i collegamenti tra strumenti.");
  }
  return body;
}

export function ensureCollegamenti() {
  if (registry) return Promise.resolve(registry);
  if (pending) return pending;
  pending = fetchCollegamentiRaw()
    .then((body) => {
      registry = body;
      pending = null;
      return registry;
    })
    .catch((error) => {
      pending = null;
      throw error;
    });
  return pending;
}

// Synchronous: `null` before the registry has loaded.
export function collegamentiSnapshot() {
  return registry;
}
