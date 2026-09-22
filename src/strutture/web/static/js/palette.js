// Command palette -- WORKBENCH_SPEC.md #6. Ctrl/Cmd+K and "/" open it; fuzzy
// search over title/summary/norm/group; recents first on empty query; full
// keyboard operation; a labelled dialog wrapping a combobox+listbox.
import { el, clear } from "./dom.js";
import { fetchTools } from "./api.js";
import { normalizeText, listRecents, trapFocus, isEditableTarget, siglaChip } from "./nav-state.js";

function fuzzyScore(text, query) {
  const hay = normalizeText(text);
  let hi = 0;
  let score = 0;
  let streak = 0;
  for (const ch of normalizeText(query)) {
    const idx = hay.indexOf(ch, hi);
    if (idx === -1) return -1;
    streak = idx === hi ? streak + 1 : 0;
    score += 10 + streak * 2 - (idx - hi);
    hi = idx + 1;
  }
  return score;
}

// WORKBENCH_SPEC §26.8: "a palette entry 'Impostazioni' (keywords: passo, arrotondamento,
// obiettivo, sfruttamento, predefiniti)" -- a fixed destination, not a tool, so it is appended
// alongside `tools` rather than fetched; `select()` below routes it the same way as a real tool.
const DESTINATIONS = [
  { name: "impostazioni", title: "Impostazioni", sigla: "IM", norm: "", summary: "passo arrotondamento obiettivo sfruttamento predefiniti" },
];

function rankTools(tools, query, recentNames) {
  const all = [...tools, ...DESTINATIONS];
  if (!query) {
    const recents = recentNames.map((name) => all.find((tool) => tool.name === name)).filter(Boolean);
    const rest = all.filter((tool) => !recentNames.includes(tool.name));
    return [...recents, ...rest];
  }
  return all
    .map((tool) => ({ tool, score: fuzzyScore(`${tool.title} ${tool.summary || ""} ${tool.norm || ""} ${tool.group || ""}`, query) }))
    .filter((entry) => entry.score >= 0)
    .sort((a, b) => b.score - a.score)
    .map((entry) => entry.tool);
}

export function initPalette({ onNavigate }) {
  const root = document.getElementById("palette-root");
  if (!root) return;

  let allTools = [];
  let loaded = false;
  let visible = [];
  let activeIndex = -1;
  let release = null;

  const input = el("input", {
    type: "text",
    id: "palette-input",
    role: "combobox",
    "aria-expanded": "true",
    "aria-controls": "palette-listbox",
    "aria-autocomplete": "list",
    "aria-labelledby": "palette-title",
    placeholder: "Cerca strumento, norma o categoria",
  });
  const listbox = el("ul", { role: "listbox", id: "palette-listbox", "aria-label": "Risultati" });
  const dialog = el("div", { class: "palette", role: "dialog", "aria-modal": "true", "aria-labelledby": "palette-title" }, [
    el("h2", { class: "palette-title", id: "palette-title", text: "Cerca uno strumento" }),
    input,
    listbox,
    el("p", { class: "palette-hint", text: "↑↓ naviga · Invio apri · Esc chiude" }),
  ]);
  const overlay = el("div", { class: "palette-overlay", hidden: true }, [dialog]);
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) close();
  });
  root.append(overlay);

  function renderOptions() {
    clear(listbox);
    if (visible.length === 0) {
      listbox.append(el("li", { class: "palette-empty", role: "presentation", text: "Nessuno strumento trovato." }));
      input.removeAttribute("aria-activedescendant");
      return;
    }
    visible.forEach((tool, index) => {
      const id = `palette-option-${index}`;
      const meta = [tool.norm, tool.summary].filter(Boolean).join(" — ");
      const titleRow = el("span", { class: "palette-option-titlerow" }, [siglaChip(tool.sigla), " ", el("span", { class: "palette-option-title", text: tool.title })]);
      const option = el(
        "li",
        { id, role: "option", "aria-selected": String(index === activeIndex), class: "palette-option", onclick: () => select(tool) },
        [titleRow, el("span", { class: "palette-option-meta", text: meta })]
      );
      listbox.append(option);
    });
    if (activeIndex >= 0) input.setAttribute("aria-activedescendant", `palette-option-${activeIndex}`);
  }

  function update() {
    visible = rankTools(allTools, input.value, listRecents(6));
    activeIndex = visible.length > 0 ? 0 : -1;
    renderOptions();
  }

  function select(tool) {
    close();
    onNavigate(tool.name);
  }

  function moveActive(delta) {
    if (visible.length === 0) return;
    activeIndex = (activeIndex + delta + visible.length) % visible.length;
    renderOptions();
  }

  function onKeydown(event) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveActive(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveActive(-1);
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (activeIndex >= 0) select(visible[activeIndex]);
    }
  }

  function open() {
    overlay.hidden = false;
    input.value = "";
    if (loaded) {
      update();
    } else {
      fetchTools()
        .then((tools) => {
          allTools = tools;
          loaded = true;
          update();
        })
        .catch(() => update());
    }
    release = trapFocus(dialog, { onEscape: close });
    input.addEventListener("keydown", onKeydown);
    input.focus();
  }

  function close() {
    overlay.hidden = true;
    input.removeEventListener("keydown", onKeydown);
    if (release) {
      release();
      release = null;
    }
  }

  input.addEventListener("input", update);

  document.addEventListener("keydown", (event) => {
    const withMeta = event.ctrlKey || event.metaKey;
    if (withMeta && event.key.toLowerCase() === "k") {
      event.preventDefault();
      if (overlay.hidden) open();
      else close();
    } else if (event.key === "/" && overlay.hidden && !isEditableTarget(event.target)) {
      event.preventDefault();
      open();
    }
  });

  // WORKBENCH_SPEC #12: the rail's own "Cerca" destination opens this same palette (js/tool-
  // index.js dispatches this instead of importing palette.js directly, keeping the two modules
  // decoupled).
  document.addEventListener("strutture:open-palette", () => {
    if (overlay.hidden) open();
  });
}
