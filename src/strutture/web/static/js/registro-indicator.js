// Per-tool registro indicators (WORKBENCH_SPEC §13.2): after the tool title, a link "N correzioni
// da confermare" (or the muted "Correzioni confermate" once every entry is decided), and -- when
// any entry for the tool was rejected -- a banner above Dati saying the standard mode still
// applies it. Data: GET /api/divergences/riepilogo, fetched once and refreshed after any sign-off
// (`strutture:registro-changed`, dispatched by registro.js on a successful save).
import { el, clear } from "./dom.js";
import { fetchRiepilogo } from "./registro-api.js";

const container = document.getElementById("tool-registro-indicator");
let riepilogo = null; // null = not loaded yet (or a fetch error) -- renders nothing rather than a stale/wrong number
let currentTool = null;

function registroLink(query, text, extraClass) {
  return el("a", { href: `#/registro?${query}`, class: extraClass ? `reg-indicator-link ${extraClass}` : "reg-indicator-link", text });
}

function render() {
  if (!container) return;
  clear(container);
  if (!currentTool || !riepilogo) return;
  const counts = riepilogo[currentTool];
  if (!counts) return;
  const pending = counts.da_confermare || 0;
  if (pending > 0) {
    const label = `${pending} correzion${pending === 1 ? "e" : "i"} da confermare`;
    container.append(registroLink(`strumento=${encodeURIComponent(currentTool)}&stato=da_confermare`, label, "reg-indicator-link--warn"));
  } else if ((counts.approvato || 0) + (counts.respinto || 0) > 0) {
    container.append(el("span", { class: "reg-indicator-muted", text: "Correzioni confermate" }));
  }
  if ((counts.respinto || 0) > 0) {
    container.append(
      el("p", { class: "reg-banner", role: "status" }, [
        el("span", { class: "reg-banner-icon", "aria-hidden": "true", text: "⚠" }),
        document.createTextNode(
          " Una correzione di questo strumento è stata respinta: la modalità standard la applica comunque. "
        ),
        registroLink(`strumento=${encodeURIComponent(currentTool)}&stato=respinto`, "Apri il registro."),
      ])
    );
  }
}

function load() {
  fetchRiepilogo()
    .then((body) => {
      riepilogo = body;
      render();
    })
    .catch(() => {
      riepilogo = null;
      render();
    });
}

document.addEventListener("strutture:tool-schema", (event) => {
  currentTool = (event.detail && event.detail.name) || null;
  if (riepilogo === null) load();
  else render();
});

document.addEventListener("strutture:registro-changed", load);
