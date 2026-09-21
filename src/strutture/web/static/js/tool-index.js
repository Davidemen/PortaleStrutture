// Tool index with search + collapsible 2-level groups -- DESIGN_SPEC.md #3.
import { el, clear } from "./dom.js";
import { readJSON, writeJSON } from "./storage.js";

function normalize(text) {
  return String(text || "")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

function haystack(tool) {
  return normalize(`${tool.title} ${tool.norm || ""} ${tool.group || ""}`);
}

function groupTools(tools) {
  const groups = [];
  const byLevel1 = new Map();
  for (const tool of tools) {
    const [level1, level2] = (tool.group || "Strumenti").split(" / ");
    if (!byLevel1.has(level1)) {
      const entry = { level1, subgroups: new Map(), order: [] };
      byLevel1.set(level1, entry);
      groups.push(entry);
    }
    const entry = byLevel1.get(level1);
    const key = level2 || "";
    if (!entry.subgroups.has(key)) {
      entry.subgroups.set(key, []);
      entry.order.push(key);
    }
    entry.subgroups.get(key).push(tool);
  }
  return groups;
}

export function renderIndex(root, tools, { onSelect }) {
  clear(root);
  const openGroups = new Set(readJSON("sm.ui.openGroups", []));
  const buttons = new Map();

  const searchInput = el("input", {
    type: "search",
    id: "tool-search",
    placeholder: "Cerca strumento o norma",
    "aria-label": "Cerca strumento o norma",
  });
  root.append(el("div", { class: "ti-search-wrap" }, [searchInput]));

  const listRoot = el("div", { class: "ti-list" });
  const emptyMessage = el("p", { class: "ti-empty", hidden: true });

  for (const group of groupTools(tools)) {
    const isOpen = openGroups.size === 0 || openGroups.has(group.level1);
    const details = el("details", { class: "ti-group", open: isOpen });
    const summary = el("summary", { text: group.level1 });
    details.append(summary);
    details.addEventListener("toggle", () => {
      const next = new Set(readJSON("sm.ui.openGroups", []));
      if (details.open) next.add(group.level1);
      else next.delete(group.level1);
      writeJSON("sm.ui.openGroups", [...next]);
    });

    for (const key of group.order) {
      const items = group.subgroups.get(key);
      const container = key ? el("div", { class: "ti-subgroup" }, [el("h3", { text: key })]) : details;
      for (const tool of items) {
        const button = el("button", {
          type: "button",
          class: "ti-item",
          "data-tool": tool.name,
          text: tool.title,
          onclick: () => onSelect(tool.name),
        });
        buttons.set(tool.name, { button, tool });
        container.append(button);
      }
      if (key) details.append(container);
    }
    listRoot.append(details);
  }

  root.append(listRoot, emptyMessage);

  function applyFilter(query) {
    const needle = normalize(query);
    let visibleCount = 0;
    for (const { button, tool } of buttons.values()) {
      const matches = !needle || haystack(tool).includes(needle);
      button.hidden = !matches;
      if (matches) visibleCount += 1;
    }
    for (const details of listRoot.querySelectorAll(".ti-group")) {
      const anyVisible = [...details.querySelectorAll(".ti-item")].some((btn) => !btn.hidden);
      details.hidden = !anyVisible;
    }
    for (const subgroup of listRoot.querySelectorAll(".ti-subgroup")) {
      const anyVisible = [...subgroup.querySelectorAll(".ti-item")].some((btn) => !btn.hidden);
      subgroup.hidden = !anyVisible;
    }
    emptyMessage.hidden = visibleCount !== 0;
    emptyMessage.textContent = visibleCount === 0 ? `Nessuno strumento per «${query}».` : "";
  }

  searchInput.addEventListener("input", () => applyFilter(searchInput.value));

  return {
    setActive(name) {
      for (const { button } of buttons.values()) {
        button.removeAttribute("aria-current");
      }
      const entry = buttons.get(name);
      if (entry) entry.button.setAttribute("aria-current", "true");
    },
    filter(query) {
      searchInput.value = query;
      applyFilter(query);
    },
  };
}
