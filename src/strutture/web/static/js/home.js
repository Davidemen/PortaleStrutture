// Home view (#/) -- WORKBENCH_SPEC.md #6: search, Preferiti, Recenti (last 6),
// then one section per category, tool cards with title/summary/norm/star.
// Fetches its own tool list (cross-package contract: "rail/home read tools
// via api.fetchTools()").
import { el, clear } from "./dom.js";
import { fetchTools } from "./api.js";
import { matchesQuery, listFavourites, listRecents, isFavourite, toggleFavourite, groupByCategory, siglaChip, nomiDaMostrare } from "./nav-state.js";
import { elencoConVoci } from "./voci.js";

function buildCard(tool, onSelect, onToggleFav) {
  const fav = isFavourite(tool.name);
  const favButton = el("button", {
    type: "button",
    class: "home-card-fav",
    "aria-pressed": String(fav),
    "aria-label": fav ? `Rimuovi ${tool.title} dai preferiti` : `Aggiungi ${tool.title} ai preferiti`,
    text: fav ? "★" : "☆",
    onclick: () => onToggleFav(tool.name),
  });
  const titleRow = el("span", { class: "home-card-titlerow" }, [siglaChip(tool.sigla), " ", el("span", { class: "home-card-title", text: tool.title })]);
  const children = [titleRow];
  if (tool.summary) children.push(el("span", { class: "home-card-summary", text: tool.summary }));
  if (tool.norm) children.push(el("span", { class: "home-card-norm", text: tool.norm }));
  const openButton = el("button", { type: "button", class: "home-card-open", onclick: () => onSelect(tool.name) }, children);
  return el("div", { class: "home-card" }, [openButton, favButton]);
}

export function renderHome(root, { onSelect }) {
  clear(root);
  const searchInput = el("input", {
    type: "search",
    id: "home-search",
    placeholder: "Cerca strumento o norma",
    "aria-label": "Cerca strumento o norma",
  });
  root.append(el("div", { class: "home-search-wrap" }, [searchInput]));
  const sectionsRoot = el("div", { class: "home-sections" });
  root.append(sectionsRoot);

  let allTools = [];

  function onToggleFav(name) {
    toggleFavourite(name);
    document.dispatchEvent(new CustomEvent("strutture:nav-state-changed"));
    build(searchInput.value);
  }

  function buildSection(heading, tools, emptyText) {
    if (tools.length === 0 && !emptyText) return null;
    const section = el("section", { class: "home-section" }, [el("h2", { text: heading })]);
    if (tools.length === 0) {
      section.append(el("p", { class: "home-empty", text: emptyText }));
      return section;
    }
    const grid = el("div", { class: "home-grid" });
    for (const tool of tools) grid.append(buildCard(tool, onSelect, onToggleFav));
    section.append(grid);
    return section;
  }

  function pick(names, source) {
    return names.map((name) => source.find((tool) => tool.name === name)).filter(Boolean);
  }

  function build(query) {
    clear(sectionsRoot);
    const filtered = allTools.filter((tool) => matchesQuery(tool, query));
    const favNames = nomiDaMostrare(listFavourites());
    const favSection = buildSection(
      "Preferiti",
      pick(favNames, filtered),
      favNames.length === 0 ? "Tocca la stella su uno strumento per aggiungerlo ai preferiti." : null
    );
    if (favSection) sectionsRoot.append(favSection);

    const recentSection = buildSection("Recenti", pick(nomiDaMostrare(listRecents(6)), filtered), null);
    if (recentSection) sectionsRoot.append(recentSection);

    const groups = groupByCategory(filtered);
    if (groups.size === 0) {
      sectionsRoot.append(el("p", { class: "home-empty", text: `Nessuno strumento per «${query}».` }));
      return;
    }
    for (const [level1, items] of groups) {
      const section = buildSection(level1, items, null);
      if (section) sectionsRoot.append(section);
    }
  }

  searchInput.addEventListener("input", () => build(searchInput.value));

  fetchTools()
    .then((tools) => {
      allTools = elencoConVoci(tools);
      build("");
    })
    .catch(() => {
      sectionsRoot.append(el("p", { class: "home-empty", text: "Impossibile caricare l'elenco degli strumenti." }));
    });
}
