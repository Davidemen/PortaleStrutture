// Cross-cutting results-sheet chrome (WORKBENCH_SPEC #4): the collapsible-group shell shared by
// results-groups.js and results-rows.js (kept here, not there, so neither of those two needs to
// import the other one's helpers -- avoids a module cycle), the toolbar strip ("Stampa relazione"
// / "Solo non soddisfatte" / "Espandi tutto", finding E: one compact row, no jump links -- the
// collapsed group headers already are the navigation) and the click-to-copy-a-value utility.
import { el, clear } from "./dom.js";
import { formatValue } from "./format.js";
import { copyText, buildManualCopyField } from "./clipboard.js";

const COPY_STATUS_MS = 1600;

export function groupId(path) {
  return `r-group-${(path || "root").replace(/\./g, "-")}`;
}

// One collapsible `<section>`: a `<button aria-expanded>` header (title · preview · badge) plus a
// body hidden with the `hidden` IDL attribute (never CSS-in-JS, never `display:none` via inline
// style). Returns a descriptor the caller fills with content and registers with the toolbar.
export function buildCollapsibleGroup(id, label, { defaultOpen = false, badge = 0, previewPairs = [] } = {}) {
  const section = el("section", { class: "r-group" });
  const bodyId = `${id}-body`;
  const header = el("button", {
    type: "button",
    class: "r-group-toggle",
    id,
    "aria-expanded": String(defaultOpen),
    "aria-controls": bodyId,
  });
  header.append(el("span", { class: "r-group-title", text: label }));
  if (previewPairs.length > 0) {
    const preview = previewPairs
      .map(({ node, value }) => `${node.symbol || node.label} ${formatValue(value, node).text}${node.unit ? ` ${node.unit}` : ""}`)
      .join(" · ");
    header.append(el("span", { class: "r-group-preview", text: preview }));
  }
  if (badge > 0) header.append(el("span", { class: "r-group-badge", text: `${badge} non soddisfatte` }));
  const body = el("div", { class: "r-group-body", id: bodyId });
  body.hidden = !defaultOpen;
  header.addEventListener("click", () => setOpen(header.getAttribute("aria-expanded") !== "true"));
  function setOpen(open) {
    header.setAttribute("aria-expanded", String(open));
    body.hidden = !open;
  }
  section.append(header, body);
  return { id, label, section, body, header, setOpen };
}

function updateGroupChrome(header, label, { badge = 0, previewPairs = [] } = {}) {
  const titleEl = header.querySelector(".r-group-title");
  if (titleEl) titleEl.textContent = label;
  let previewEl = header.querySelector(".r-group-preview");
  if (previewPairs.length > 0) {
    const text = previewPairs
      .map(({ node, value }) => `${node.symbol || node.label} ${formatValue(value, node).text}${node.unit ? ` ${node.unit}` : ""}`)
      .join(" · ");
    if (!previewEl) {
      previewEl = el("span", { class: "r-group-preview" });
      header.insertBefore(previewEl, header.querySelector(".r-group-badge") || null);
    }
    previewEl.textContent = text;
  } else if (previewEl) {
    previewEl.remove();
  }
  let badgeEl = header.querySelector(".r-group-badge");
  if (badge > 0) {
    if (!badgeEl) {
      badgeEl = el("span", { class: "r-group-badge" });
      header.append(badgeEl);
    }
    badgeEl.textContent = `${badge} non soddisfatte`;
  } else if (badgeEl) {
    badgeEl.remove();
  }
}

// Print-only group chrome (WORKBENCH_SPEC §10): a plain heading, never a `<button>` ("nothing
// interactive... no buttons" in a printed report), body always visible (print has no fold/filter
// state to hide behind). `id` is prefixed by the caller (`mountGroup` below) so it can never
// collide with the SAME group's id in the interactive tree still on screen -- `document.
// getElementById` is never called on the print path at all, on purpose (see `mountGroup`).
function buildGroupChromePrint(id, label) {
  const section = el("section", { class: "r-group r-group--print" });
  section.append(el("h3", { class: "r-group-title", text: label }));
  const body = el("div", { class: "r-group-body", id: `${id}-body` });
  section.append(body);
  return { id, label, section, body, header: null, setOpen: () => {} };
}

// Live-calculation reconciliation (WORKBENCH_SPEC #2): finds the group by `id` if a previous
// render already mounted it and only refreshes its header text -- the section/body DOM node is
// never recreated, so its open/closed state, scroll position and focus survive untouched. Only a
// genuinely new group is appended to `parent`. The caller still rebuilds the group's ROW content
// each time (cheap; each row's own change is flagged separately via `data-changed`), but the
// group's own identity in the DOM tree stays stable across runs -- nothing above the row level is
// ever re-mounted.
//
// `opts.print`: builds fresh into `parent` EVERY time instead (a print document has no previous
// render to reconcile against) via `buildGroupChromePrint`, under an id prefixed `p-` so it can
// never collide with -- and so must never risk `document.getElementById`-adopting -- the SAME
// group's node in the interactive tree elsewhere in the document.
export function mountGroup(parent, id, label, opts = {}) {
  if (opts.print) {
    const built = buildGroupChromePrint(`p-${id}`, label);
    parent.append(built.section);
    return { ...built, reused: false };
  }
  const existingHeader = document.getElementById(id);
  if (existingHeader) {
    updateGroupChrome(existingHeader, label, opts);
    const body = document.getElementById(`${id}-body`);
    const section = existingHeader.closest(".r-group") || existingHeader;
    // The caller's own body was just `clear()`-ed (results-groups.js/results-rows.js rebuild
    // their row content every render), which detaches any reused NESTED group along with it --
    // `append` on an already-attached node just moves it, so this both re-parents a detached
    // group and keeps build order correct either way.
    parent.append(section);
    const setOpen = (open) => {
      existingHeader.setAttribute("aria-expanded", String(open));
      if (body) body.hidden = !open;
    };
    return { id, label, header: existingHeader, body, section, setOpen, reused: true };
  }
  const built = buildCollapsibleGroup(id, label, opts);
  parent.append(built.section);
  return { ...built, reused: false };
}

// Removes a previously-mounted group that no longer has any content to show (e.g. every value in
// it went null on this run) -- mirrors the old "don't append an empty group" rule.
export function unmountGroup(id) {
  const header = document.getElementById(id);
  const section = header ? header.closest(".r-group") : null;
  if (section) section.remove();
}

// One `role=status` node per results root, created once and reused across renders, so "Copiato"
// is announced next to where the click happened -- not a page-level toast (DESIGN_SPEC #0).
// `announce()` also accepts a DOM node (WORKBENCH_SPEC clipboard fix, 2026-09-21): a failed copy
// -- plain http, no `navigator.clipboard` -- shows a manual-copy field instead of text, so a
// click on a table/table-row cell never claims "Copiato" when nothing was actually copied.
export function createCopyStatus(root) {
  let statusEl = root.querySelector(":scope > .r-copy-status");
  if (!statusEl) {
    statusEl = el("div", { class: "r-copy-status", role: "status" });
    root.prepend(statusEl);
  }
  let timer = null;
  function announce(content) {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    clear(statusEl);
    if (typeof content === "string") {
      statusEl.textContent = content;
      timer = setTimeout(() => {
        statusEl.textContent = "";
      }, COPY_STATUS_MS);
    } else {
      statusEl.append(content);
    }
  }
  return { statusEl, announce };
}

// Click (or Enter/Space) on a value cell copies it at full precision (WORKBENCH_SPEC #4).
export function wireValueCopy(cellEl, copyValue, announce) {
  if (!copyValue) return;
  cellEl.classList.add("r-cell-value--copy");
  cellEl.tabIndex = 0;
  cellEl.setAttribute("role", "button");
  cellEl.setAttribute("aria-label", `Copia il valore ${copyValue}`);
  const trigger = async () => {
    const ok = await copyText(copyValue);
    announce(ok ? "Copiato" : buildManualCopyField(copyValue, "Valore"));
  };
  cellEl.addEventListener("click", trigger);
  cellEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      trigger();
    }
  });
}

// `groups` = [{id, label, setOpen}] collected while building the groups; `onFilterChange(only)`
// flips the Verifiche group's row filter. `printBtn`, when given, joins the SAME row (finding E:
// one compact toolbar, not three stacked buttons above a jump-link strip).
export function buildToolbar({ groups, onFilterChange, hasChecks, printBtn }) {
  const bar = el("div", { class: "r-toolbar" });

  if (printBtn) bar.append(printBtn);

  if (hasChecks) {
    const filterBtn = el("button", {
      type: "button",
      class: "r-action r-toolbar-filter",
      "aria-pressed": "false",
      text: "Solo non soddisfatte",
    });
    filterBtn.addEventListener("click", () => {
      const next = filterBtn.getAttribute("aria-pressed") !== "true";
      filterBtn.setAttribute("aria-pressed", String(next));
      onFilterChange(next);
    });
    bar.append(filterBtn);
  }

  if (groups.length > 0) {
    const expandBtn = el("button", { type: "button", class: "r-action", text: "Espandi tutto" });
    expandBtn.addEventListener("click", () => {
      const collapseNow = expandBtn.textContent === "Comprimi tutto";
      for (const group of groups) group.setOpen(!collapseNow);
      expandBtn.textContent = collapseNow ? "Espandi tutto" : "Comprimi tutto";
    });
    bar.append(expandBtn);
  }

  return bar;
}
