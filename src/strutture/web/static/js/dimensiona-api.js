// Thin fetch wrappers for `POST /api/tools/{name}/dimensiona` and `.../sensibilita`
// (WORKBENCH_SPEC §23.4/§24.1). Same error-surfacing convention as js/registro-api.js: every
// function returns `{ok, status, body}` rather than throwing on a 4xx/5xx -- the dialogs need the
// Italian message AND the status code (429 vs 422 read differently) to decide what to show.
async function readJson(response) {
  try {
    return await response.json();
  } catch (error) {
    return { ok: false, errors: ["Risposta del server non valida."] };
  }
}

async function post(url, payload, signal) {
  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
  } catch (error) {
    if (error && error.name === "AbortError") throw error;
    return { ok: false, status: 0, body: { errors: ["Impossibile contattare il server."] } };
  }
  const body = await readJson(response);
  return { ok: response.status === 200, status: response.status, body };
}

export function postDimensiona(toolName, payload, signal) {
  return post(`/api/tools/${encodeURIComponent(toolName)}/dimensiona`, payload, signal);
}

export function postSensibilita(toolName, payload, signal) {
  return post(`/api/tools/${encodeURIComponent(toolName)}/sensibilita`, payload, signal);
}
