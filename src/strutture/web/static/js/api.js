// Thin fetch wrappers for the /api/tools endpoints. No framework, no CDN.

async function readJson(response) {
  const body = await response.json();
  return { status: response.status, body };
}

export async function fetchTools() {
  const response = await fetch("/api/tools");
  const { body } = await readJson(response);
  return body;
}

export async function fetchSchema(toolName) {
  const response = await fetch(`/api/tools/${encodeURIComponent(toolName)}/schema`);
  const { status, body } = await readJson(response);
  if (status !== 200) {
    throw new Error(body.errors ? body.errors.join(" ") : "Impossibile caricare lo schema.");
  }
  return body;
}

export async function searchComuni(query) {
  try {
    const response = await fetch(`/api/comuni?q=${encodeURIComponent(query)}`);
    return response.ok ? await response.json() : [];
  } catch (error) {
    return []; // suggestions are best-effort: the field still accepts free text
  }
}

export async function runTool(toolName, inputs) {
  const response = await fetch(`/api/tools/${encodeURIComponent(toolName)}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(inputs),
  });
  const { status, body } = await readJson(response);
  return { status, report: body };
}
