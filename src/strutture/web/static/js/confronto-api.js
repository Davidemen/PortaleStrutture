// Thin fetch wrapper for `POST /api/tools/{name}/compare` (WORKBENCH_SPEC §13.3): the current
// inputs run in both modes (code-standard and the Excel-compatible legacy branch) in one request.
// Errors are never swallowed -- every failure throws a plain Error with an Italian message.
export async function fetchCompare(toolName, values) {
  let response;
  try {
    response = await fetch(`/api/tools/${encodeURIComponent(toolName)}/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
    });
  } catch (error) {
    throw new Error("Impossibile contattare il server.");
  }
  let body;
  try {
    body = await response.json();
  } catch (error) {
    throw new Error("Risposta del server non valida.");
  }
  if (response.status !== 200) {
    throw new Error((body && Array.isArray(body.errors) && body.errors[0]) || "Errore del server durante il confronto.");
  }
  return body; // {ok, disponibile, standard, excel, confronto}
}
