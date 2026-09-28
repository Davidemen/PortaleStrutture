// Navigation state shared by the rail, Home and the palette -- WORKBENCH_SPEC.md #6/#12.
// Favourites/recents in localStorage (sm.nav.fav, sm.nav.recent); plain-substring
// search matching; a small focus-trap helper reused by the palette and the
// shortcuts sheet (both are CSP-safe overlay dialogs built the same way); the sigla chip and
// category grouping/ordering shared by the rail, Home and the palette (WORKBENCH_SPEC #12: the
// chip "is also shown on Home cards, in the palette rows and next to the tool title").
import { el } from "./dom.js";
import { readJSON, writeJSON } from "./storage.js";
import { rappresentante, nomiUnici } from "./voci.js";

const FAV_KEY = "sm.nav.fav";
const RECENT_KEY = "sm.nav.recent";
const RECENT_MAX = 20;

// WORKBENCH_SPEC #12: "the FIVE categories (Carichi, Calcestruzzo armato, Acciaio, Geotecnica,
// Fondazioni)" -- a fixed order the design lead specified, not just first-appearance order.
const CATEGORY_ORDER = ["Carichi", "Calcestruzzo armato", "Acciaio", "Geotecnica", "Fondazioni"];

export function isEditableTarget(target) {
  if (!target) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || Boolean(target.isContentEditable);
}

export function normalizeText(text) {
  return String(text || "")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

export function matchesQuery(tool, query) {
  const needle = normalizeText(query);
  if (!needle) return true;
  const haystack = normalizeText(`${tool.title} ${tool.summary || ""} ${tool.norm || ""} ${tool.group || ""} ${tool.cerca || ""}`);
  return haystack.includes(needle);
}

export function listFavourites() {
  return readJSON(FAV_KEY, []);
}

// WORKBENCH_SPEC §27.5: favourites/recents stay stored per TOOL (colleagues' lists stay valid) but
// an entry is one row: any of its parts starred = the entry starred; un-starring it drops them all.
export function isFavourite(name) {
  return listFavourites().some((item) => rappresentante(item) === rappresentante(name));
}

export function toggleFavourite(name) {
  const current = listFavourites();
  const was = isFavourite(name);
  const next = was ? current.filter((item) => rappresentante(item) !== rappresentante(name)) : [...current, name];
  writeJSON(FAV_KEY, next);
  return !was;
}

// The names to show in Preferiti/Recenti lists: one per entry, in stored order.
export function nomiDaMostrare(names) {
  return nomiUnici(names);
}

export function listRecents(limit = 6) {
  return readJSON(RECENT_KEY, []).slice(0, limit);
}

export function addRecent(name) {
  if (!name) return;
  const current = readJSON(RECENT_KEY, []).filter((item) => item !== name);
  const next = [name, ...current].slice(0, RECENT_MAX);
  writeJSON(RECENT_KEY, next);
}

// Traps Tab/Shift+Tab inside `container`, calls `onEscape()` on Escape, and
// restores focus to whatever had it when the trap was installed. Returns a
// release() to call when the dialog closes normally (e.g. a selection).
export function trapFocus(container, { onEscape } = {}) {
  const previous = document.activeElement;

  function focusable() {
    return [
      ...container.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ),
    ].filter((el) => el.offsetParent !== null || el === document.activeElement);
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      if (onEscape) onEscape();
      return;
    }
    if (event.key !== "Tab") return;
    const items = focusable();
    if (items.length === 0) {
      event.preventDefault();
      return;
    }
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  container.addEventListener("keydown", onKeydown);

  return function release() {
    container.removeEventListener("keydown", onKeydown);
    if (previous && typeof previous.focus === "function") previous.focus({ preventScroll: true });
  };
}

export function categoryOf(tool) {
  return (tool.group || "Strumenti").split(" / ")[0];
}

// Tools grouped by their top-level category, ordered per CATEGORY_ORDER (any category not in
// that fixed list -- future work -- sorts after, in first-seen order).
export function groupByCategory(tools) {
  const groups = new Map();
  for (const tool of tools) {
    const key = categoryOf(tool);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(tool);
  }
  const ordered = new Map();
  for (const key of CATEGORY_ORDER) if (groups.has(key)) ordered.set(key, groups.get(key));
  for (const [key, items] of groups) if (!ordered.has(key)) ordered.set(key, items);
  return ordered;
}

// 28x20px rounded-outline chip in tabular capitals (WORKBENCH_SPEC #12) -- shown on rail rows,
// Home cards, palette rows and next to the tool title. `tool.sigla` is always populated by the
// backend (`GET /api/tools`, falls back there to the first two letters of the title).
export function siglaChip(sigla) {
  return el("span", { class: "sm-sigla-chip", text: sigla || "?" });
}

// One compact tool row shared by the rail's flyouts and its expanded accordions
// (WORKBENCH_SPEC #12): sigla chip + title (2 lines max, CSS line-clamp) + norm in small type +
// a (star) toggle that never triggers navigation. Returns the row `<li>` plus the primary "open"
// button (for keyboard roving / `aria-current` marking) so callers never have to re-query it.
export function buildToolRow(tool, { onSelect, onToggleFav, active = false } = {}) {
  // Review finding 23: `.rail-row-norm` (nav.css) is hidden in the rail itself (it turned a
  // 2-line title into 4 lines) -- the norm still reaches the engineer as a hover tooltip here.
  const hoverTitle = tool.norm ? `${tool.title} — ${tool.norm}` : tool.title;
  const openButton = el(
    "button",
    {
      type: "button",
      class: "rail-row-open",
      "data-tool": tool.name,
      "data-title": tool.title,
      title: hoverTitle,
      "aria-current": active ? "true" : undefined,
      onclick: () => onSelect(tool.name),
    },
    [
      siglaChip(tool.sigla),
      " ",
      el("span", { class: "rail-row-text" }, [
        el("span", { class: "rail-row-title", text: tool.title }),
        el("span", { class: "rail-row-norm", text: tool.norm || "" }),
      ]),
    ]
  );
  const fav = isFavourite(tool.name);
  const favButton = el("button", {
    type: "button",
    class: "rail-row-fav",
    "aria-pressed": String(fav),
    "aria-label": fav ? `Rimuovi ${tool.title} dai preferiti` : `Aggiungi ${tool.title} ai preferiti`,
    text: fav ? "★" : "☆",
    onclick: () => onToggleFav(tool.name),
  });
  const row = el("li", { class: "rail-row" }, [openButton, favButton]);
  return { row, openButton };
}

// A flyout/accordion's rows, grouped by sub-heading (WORKBENCH_SPEC #12: "tools grouped by
// sub-group ('Neve', 'Sisma', 'Vento')"). Within one category the heading is just the sub-group;
// Preferiti/Recenti can cross categories, so their heading is the tool's full group path.
// Returns a fragment ready to append plus the ordered "open" buttons (for keyboard roving).
function subHeading(tool, ownTitle) {
  const group = tool.group || "";
  const [level1, ...rest] = group.split(" / ");
  if (level1 === ownTitle && rest.length > 0) return rest.join(" / ");
  return group || "Altro";
}

export function buildRowSections(tools, { ownTitle, onSelect, onToggleFav, activeName }) {
  const fragment = document.createDocumentFragment();
  const rowButtons = [];
  if (tools.length === 0) {
    fragment.append(el("p", { class: "rail-flyout-empty", text: "Nessuno strumento qui per ora." }));
    return { fragment, rowButtons };
  }
  const sections = new Map();
  for (const tool of tools) {
    const heading = subHeading(tool, ownTitle);
    if (!sections.has(heading)) sections.set(heading, []);
    sections.get(heading).push(tool);
  }
  for (const [heading, items] of sections) {
    if (sections.size > 1) fragment.append(el("h3", { class: "rail-flyout-heading", text: heading }));
    const list = el("ul", { class: "rail-row-list" });
    for (const tool of items) {
      const { row, openButton } = buildToolRow(tool, { onSelect, onToggleFav, active: tool.name === activeName });
      list.append(row);
      rowButtons.push(openButton);
    }
    fragment.append(list);
  }
  return { fragment, rowButtons };
}
