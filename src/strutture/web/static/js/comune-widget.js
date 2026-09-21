// Searchable comune dropdown: a text input backed by a <datalist> filled from /api/comuni.
// Option values are the unique labels the tools accept ("Castro (Lecce)" for homonyms).
import { searchComuni } from "./api.js";
import { clear, el } from "./dom.js";

const MIN_QUERY_LENGTH = 2;
const DEBOUNCE_MS = 200;

function buildOption(option) {
  return el("option", { value: option.label, label: `${option.provincia} — ${option.regione}` });
}

export function buildComuneInput(field, id, describedById) {
  const listId = `${id}-options`;
  const datalist = el("datalist", { id: listId });
  const input = el("input", {
    type: "text",
    id,
    name: field.name,
    list: listId,
    autocomplete: "off",
    placeholder: "Digita le prime lettere…",
    required: field.required,
    "aria-describedby": describedById,
  });

  let timer = null;
  let latestQuery = "";
  input.addEventListener("input", () => {
    const query = input.value.trim();
    clearTimeout(timer);
    if (query.length < MIN_QUERY_LENGTH) {
      clear(datalist);
      return;
    }
    timer = setTimeout(async () => {
      latestQuery = query;
      const options = await searchComuni(query);
      if (latestQuery !== query) return; // a newer keystroke superseded this response
      datalist.replaceChildren(...options.map(buildOption));
    }, DEBOUNCE_MS);
  });

  const wrapper = el("div", { class: "comune-widget" }, [input, datalist]);
  return wrapper;
}
