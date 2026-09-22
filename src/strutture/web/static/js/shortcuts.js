// Global keyboard shortcuts -- WORKBENCH_SPEC.md #6: g h home, Ctrl+Enter run,
// [ / ] previous/next Dati section, Alt+1/2 focus Dati/Risultati, ? opens the
// shortcut sheet. Ignored while typing in a field (except Ctrl+Enter, which
// must work anywhere per WORKBENCH_SPEC #2).
import { el } from "./dom.js";
import { isEditableTarget, trapFocus } from "./nav-state.js";
import { focusResults, focusDati } from "./layout.js";

const SHORTCUTS = [
  { keys: "g h", desc: "Vai alla Home" },
  { keys: "Ctrl+Invio", desc: "Esegui il calcolo" },
  { keys: "[ / ]", desc: "Sezione dati precedente/successiva" },
  { keys: "Alt+1", desc: "Vai a Dati" },
  { keys: "Alt+2", desc: "Vai a Risultati" },
  { keys: "Ctrl/Cmd+K oppure /", desc: "Apri la ricerca strumenti" },
  // WORKBENCH_SPEC §21.1: the keys themselves belong to js/annulla-ui.js's own document-level
  // keydown listener (native-first while typing) -- this sheet only lists them.
  { keys: "Ctrl/Cmd+Z", desc: "Annulla l'ultima modifica ai dati" },
  { keys: "Ctrl/Cmd+Shift+Z oppure Ctrl+Y", desc: "Ripristina la modifica annullata" },
  { keys: "?", desc: "Mostra questa guida" },
];

function buildSheet(onClose) {
  const list = el("div", { class: "shortcuts-list" });
  for (const item of SHORTCUTS) {
    list.append(el("div", {}, [el("kbd", { text: item.keys }), el("span", { text: item.desc })]));
  }
  const closeButton = el("button", { type: "button", class: "shortcuts-close", text: "Chiudi", onclick: onClose });
  const sheet = el("div", { class: "shortcuts-sheet", role: "dialog", "aria-modal": "true", "aria-labelledby": "shortcuts-title" }, [
    el("h2", { id: "shortcuts-title", text: "Scorciatoie da tastiera" }),
    list,
    closeButton,
  ]);
  return { sheet, closeButton };
}

// forms-live builds each Dati section as `<section class="f-section"><h3><button
// class="f-section-toggle" aria-expanded aria-controls>...` (WORKBENCH_SPEC §3), not a native
// `<details>` -- only the closed "Avanzate" fold at the end is a real `<details><summary>`. Both
// disclosure kinds are included here, in DOM order, so `[`/`]` walks every section header.
function moveSection(delta) {
  const headers = [...document.querySelectorAll("#form-root .f-section-toggle, #form-root .f-advanced > summary")];
  if (headers.length === 0) return;
  const currentIndex = headers.indexOf(document.activeElement);
  const nextIndex = currentIndex === -1 ? 0 : (currentIndex + delta + headers.length) % headers.length;
  headers[nextIndex].focus();
  headers[nextIndex].scrollIntoView({ block: "nearest" });
}

function runForm() {
  const form = document.querySelector("#form-root form");
  if (form) form.requestSubmit();
}

export function initShortcuts({ onHome }) {
  const root = document.getElementById("shortcuts-root");
  if (!root) return;

  let release = null;
  function close() {
    overlay.hidden = true;
    if (release) {
      release();
      release = null;
    }
  }
  const { sheet, closeButton } = buildSheet(close);
  const overlay = el("div", { class: "shortcuts-overlay", hidden: true }, [sheet]);
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) close();
  });
  root.append(overlay);

  function open() {
    overlay.hidden = false;
    release = trapFocus(sheet, { onEscape: close });
    closeButton.focus();
  }

  let pendingG = false;
  let pendingTimer = null;

  document.addEventListener("keydown", (event) => {
    if (event.defaultPrevented) return;

    if (!overlay.hidden) {
      if (event.key === "?") {
        event.preventDefault();
        close();
      }
      return;
    }

    if (event.ctrlKey && event.key === "Enter") {
      event.preventDefault();
      runForm();
      return;
    }
    if (event.altKey && event.key === "1") {
      event.preventDefault();
      focusDati();
      return;
    }
    if (event.altKey && event.key === "2") {
      event.preventDefault();
      focusResults();
      return;
    }
    if (isEditableTarget(event.target) || event.ctrlKey || event.metaKey || event.altKey) return;

    if (event.key === "?") {
      event.preventDefault();
      open();
    } else if (event.key === "g") {
      pendingG = true;
      clearTimeout(pendingTimer);
      pendingTimer = setTimeout(() => {
        pendingG = false;
      }, 600);
    } else if (event.key === "h" && pendingG) {
      pendingG = false;
      event.preventDefault();
      onHome();
    } else if (event.key === "[") {
      event.preventDefault();
      moveSection(-1);
    } else if (event.key === "]") {
      event.preventDefault();
      moveSection(1);
    }
  });
}
