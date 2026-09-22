// Rail navigation, redesigned (WORKBENCH_SPEC.md #12, user feedback: "icons are all the same;
// collapsed it is almost impossible to navigate"). Collapsed (56px) = an activity bar of
// destinations -- Home, Cerca, Preferiti, Recenti, "Registro correzioni" (WORKBENCH_SPEC §13.1),
// the five categories -- + the expand/collapse toggle, NO individual tools; a category/Preferiti/
// Recenti button opens a 280px flyout (js/rail-flyout.js) listing its tools; Registro is a plain
// destination link (like Home), not a flyout. Expanded (240px, >=1100px only) shows the same
// destinations with text; Preferiti/Recenti/categories become accordions instead of flyouts.
// 720-1099px forces the collapsed activity bar (css/layout.css already pins the grid column
// width there); <720px the mobile picker (layout.js relocates this whole <nav>) always gets the
// expanded/accordion style at full width -- no space pressure inside a full-width dropdown.
// Fetches its own tool list (cross-package contract: "rail/home read tools via api.fetchTools()").
import { el, clear } from "./dom.js";
import { readJSON, writeJSON } from "./storage.js";
import { fetchTools } from "./api.js";
import { fetchTotalePendenti } from "./registro-api.js";
import { buildIcon } from "./icons.js";
import { createFlyout } from "./rail-flyout.js";
import { groupByCategory, categoryOf, listFavourites, listRecents, toggleFavourite, buildRowSections } from "./nav-state.js";

const CATEGORY_ICONS = {
  Carichi: "carichi",
  "Calcestruzzo armato": "calcestruzzo-armato",
  Acciaio: "acciaio",
  Geotecnica: "geotecnica",
  Fondazioni: "fondazioni",
};

const wideQuery = window.matchMedia("(min-width: 1100px)");
const narrowQuery = window.matchMedia("(max-width: 719.98px)");

function setRailCollapsed(collapsed) {
  const app = document.getElementById("app");
  if (app) app.classList.toggle("rail-collapsed", collapsed);
}

// >=1100px: the user's own 56/240px toggle (`sm.ui.rail`). 720-1099px: forced collapsed. <720px:
// the mobile picker always gets the expanded/accordion style (there is no width pressure inside
// a full-width dropdown, and it needs to "gain the sigla chips and the category pictograms").
function isCollapsedMode() {
  if (narrowQuery.matches) return false;
  if (!wideQuery.matches) return true;
  return readJSON("sm.ui.rail", "expanded") === "collapsed";
}

function loadOpenGroups() {
  const raw = readJSON("sm.ui.openGroups", null);
  return raw && typeof raw === "object" && !Array.isArray(raw) ? raw : {};
}
function saveOpenGroup(key, open) {
  writeJSON("sm.ui.openGroups", { ...loadOpenGroups(), [key]: open });
}

export function renderIndex(root, { onSelect }) {
  let allTools = [];
  let currentName = null;
  let loadError = false;
  let pendingCount = 0;
  const flyout = createFlyout();

  function loadPendingCount() {
    fetchTotalePendenti()
      .then((count) => {
        pendingCount = count;
        refreshDynamic();
      })
      .catch(() => {
        /* the badge stays at its last known count (or 0) -- a failed refresh is not worth an error state on the whole rail */
      });
  }

  function onToggleFav(name) {
    toggleFavourite(name);
    document.dispatchEvent(new CustomEvent("strutture:nav-state-changed"));
  }

  function toolsFor(kind) {
    if (kind.type === "category") return allTools.filter((tool) => categoryOf(tool) === kind.title);
    const names = kind.type === "preferiti" ? listFavourites() : listRecents(5);
    return names.map((name) => allTools.find((tool) => tool.name === name)).filter(Boolean);
  }

  function groupContainsActive(kind) {
    return currentName != null && toolsFor(kind).some((tool) => tool.name === currentName);
  }

  function selectAndClose(name) {
    onSelect(name);
    flyout.close({ restoreFocus: false });
  }

  // Review finding 23 ("the active tool is yellow twice"): the active tool's OWN row is marker-
  // highlighted only inside its category listing -- Preferiti/Recenti almost always contain that
  // SAME tool too (it was just navigated to), which used to highlight it a second time there,
  // reading as two unrelated "active" rows instead of one.
  function rowsActiveName(kind) {
    return kind.type === "category" ? currentName : null;
  }

  function buildFlyoutTrigger(kind) {
    const iconWrap = el("span", { class: "rail-icon" }, [buildIcon(kind.icon)]);
    let hoverTitle = kind.title;
    if (kind.type === "category" && groupContainsActive(kind)) {
      const activeTool = allTools.find((tool) => tool.name === currentName);
      const sigla = (activeTool && activeTool.sigla) || "?";
      iconWrap.append(el("span", { class: "rail-sigla-badge", text: sigla }));
      hoverTitle = `${kind.title} — strumento attivo: ${sigla}`;
    }
    const button = el(
      "button",
      { type: "button", class: "rail-item", title: hoverTitle, "aria-haspopup": "dialog", "aria-expanded": "false" },
      [iconWrap, el("span", { class: "rail-label", text: kind.title })]
    );
    if (kind.type === "category" && groupContainsActive(kind)) button.classList.add("rail-item--active-category");

    function openThis() {
      if (flyout.isOpen() && flyout.activeTrigger() === button) {
        flyout.close({ restoreFocus: false });
        return;
      }
      button.setAttribute("aria-expanded", "true");
      flyout.open({
        trigger: button,
        title: kind.title,
        buildBody: (bodyEl) => {
          const { fragment, rowButtons } = buildRowSections(toolsFor(kind), {
            ownTitle: kind.title,
            onSelect: selectAndClose,
            onToggleFav,
            activeName: rowsActiveName(kind),
          });
          bodyEl.append(fragment);
          return rowButtons;
        },
        onClose: () => button.setAttribute("aria-expanded", "false"),
      });
    }
    button.addEventListener("click", openThis);
    button.addEventListener("keydown", (event) => {
      if (event.key === "ArrowRight") {
        event.preventDefault();
        openThis();
      }
    });
    return button;
  }

  function buildAccordion(kind) {
    const state = loadOpenGroups();
    // Review finding 23: Recenti almost always contains the tool that is CURRENTLY open (it was
    // just navigated to) -- defaulting it open the same way a category does re-opened it on every
    // single navigation, pushing the categories below it off-screen. Recenti only ever
    // default-opens from an explicit user toggle now; Preferiti/categories are unaffected.
    const defaultOpen = kind.type === "recenti" ? false : groupContainsActive(kind);
    const isOpen = kind.title in state ? state[kind.title] : defaultOpen;
    const details = el("details", { class: "rail-group", open: isOpen, "data-kind": kind.type });
    details.append(
      el("summary", {}, [el("span", { class: "rail-icon" }, [buildIcon(kind.icon)]), el("span", { class: "rail-label", text: kind.title })])
    );
    details.addEventListener("toggle", () => saveOpenGroup(kind.title, details.open));
    const { fragment } = buildRowSections(toolsFor(kind), { ownTitle: kind.title, onSelect, onToggleFav, activeName: rowsActiveName(kind) });
    const list = el("div", { class: "rail-group-list" });
    list.append(fragment);
    details.append(list);
    return details;
  }

  function buildNavButton({ title, icon, hint, onClick, current, badge = 0 }) {
    const iconWrap = el("span", { class: "rail-icon" }, [buildIcon(icon)]);
    // `badge` (WORKBENCH_SPEC §13.1's "count chip", currently only "Registro correzioni"), in two
    // places and css/nav.css shows exactly one: a corner badge on the icon when the rail is
    // collapsed (the icon is all there is), a plain count at the END of the row when it is expanded
    // -- a three-digit badge sitting on the pictogram hid the very icon that identifies the entry.
    const children = [iconWrap, el("span", { class: "rail-label", text: title })];
    if (badge > 0) {
      iconWrap.append(el("span", { class: "rail-pending-badge", "aria-hidden": "true", text: String(badge) }));
      children.push(el("span", { class: "rail-pending-count", text: String(badge), title: `${badge} da confermare` }));
    }
    return el(
      "button",
      {
        type: "button",
        class: "rail-item",
        title: hint ? `${title} (${hint})` : title,
        "aria-current": current ? "true" : undefined,
        onclick: onClick,
      },
      children
    );
  }

  function buildToggle(collapsedNow) {
    const label = collapsedNow ? "Espandi la barra di navigazione" : "Comprimi la barra di navigazione";
    return el(
      "button",
      {
        type: "button",
        class: "rail-toggle",
        "aria-label": label,
        title: label,
        onclick: () => {
          writeJSON("sm.ui.rail", collapsedNow ? "expanded" : "collapsed");
          render();
        },
      },
      [buildIcon(collapsedNow ? "espandi" : "comprimi")]
    );
  }

  function render() {
    const collapsed = isCollapsedMode();
    flyout.close({ restoreFocus: false });
    clear(root);
    // `.rail-collapsed` drives the icon-only 56px look (css/nav.css, unscoped by width -- the
    // GRID column width itself is pinned by css/layout.css's own media queries): it must track
    // whichever markup is actually rendered, at every breakpoint, not just the >=1100px range
    // the user's own toggle applies to.
    setRailCollapsed(collapsed);

    const list = el("div", { class: "rail-list" });
    list.append(buildNavButton({ title: "Home", icon: "home", onClick: () => onSelect(""), current: !currentName }));
    list.append(
      buildNavButton({
        title: "Cerca",
        icon: "cerca",
        hint: "Ctrl K",
        onClick: () => document.dispatchEvent(new CustomEvent("strutture:open-palette")),
      })
    );

    const groupKinds = [
      { type: "preferiti", title: "Preferiti", icon: "preferiti" },
      { type: "recenti", title: "Recenti", icon: "recenti" },
    ];
    groupKinds.forEach((kind) => list.append(collapsed ? buildFlyoutTrigger(kind) : buildAccordion(kind)));

    // "Rail: one fixed entry 'Registro correzioni' below Recenti" (WORKBENCH_SPEC §13.1) -- a
    // plain destination link like Home, not a flyout/accordion (it has no "its own tools" list).
    list.append(
      buildNavButton({
        title: "Registro correzioni",
        icon: "registro",
        onClick: () => onSelect("registro"),
        current: currentName === "registro",
        badge: pendingCount,
      })
    );
    // "Rail: fixed entry 'Progetti' below 'Registro correzioni'" (WORKBENCH_SPEC §14.1), the same
    // plain-destination pattern -- current for BOTH #/progetti (list) and #/progetti/<id>
    // (project page), since main.js's `indexApi.setActive("progetti")` covers either route.
    list.append(
      buildNavButton({
        title: "Progetti",
        icon: "progetti",
        onClick: () => onSelect("progetti"),
        current: currentName === "progetti",
      })
    );

    const categoryKinds = [...groupByCategory(allTools)].map(([level1]) => ({ type: "category", title: level1, icon: CATEGORY_ICONS[level1] || "progetti" }));
    categoryKinds.forEach((kind, index) => {
      const node = collapsed ? buildFlyoutTrigger(kind) : buildAccordion(kind);
      if (index === 0) node.classList.add("rail-sep-before");
      list.append(node);
    });

    if (loadError) list.append(el("p", { class: "rail-empty", text: "Impossibile caricare l'elenco degli strumenti." }));

    root.append(list, buildToggle(collapsed));
  }

  // Favourites/recents changed: refresh in place when a flyout is open (WORKBENCH_SPEC #12 --
  // starring a tool from inside an open Preferiti/Recenti flyout must update the list, not slam
  // the dialog shut); otherwise a full render is cheap and there is nothing open to disrupt.
  function refreshDynamic() {
    if (flyout.isOpen()) flyout.refresh();
    else render();
  }

  fetchTools()
    .then((tools) => {
      allTools = tools;
      render();
    })
    .catch(() => {
      loadError = true;
      render();
    });
  loadPendingCount();

  wideQuery.addEventListener("change", render);
  narrowQuery.addEventListener("change", render);
  document.addEventListener("strutture:nav-state-changed", refreshDynamic);
  // A sign-off (single or bulk, js/registro.js) changes the pending count -- refetch it so the
  // badge (and the per-tool indicator, js/registro-indicator.js, listening to the SAME event)
  // never goes stale after a decision the engineer just made.
  document.addEventListener("strutture:registro-changed", loadPendingCount);

  return {
    setActive(name) {
      currentName = name || null;
      // A real navigation (deep link, "g h", a palette pick, ...) makes whatever flyout is open
      // stale -- close it rather than leaving it floating over the new page (it did not get the
      // normal close-on-select treatment, since it was not the thing that triggered this route
      // change).
      flyout.close({ restoreFocus: false });
      refreshDynamic();
    },
  };
}
