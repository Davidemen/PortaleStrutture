// Pure diffing + view-state preservation for live re-renders (WORKBENCH_SPEC #2). When the output
// TREE SHAPE hasn't changed between two runs, results.js patches value cells in place instead of
// clearing and rebuilding -- which is what actually keeps scroll position, open groups and focus
// untouched (they're just never removed). Structure changes (a field/group appears or disappears,
// a rows array changes length) fall back to a full re-mount.
import { readPath } from "./output-schema.js";

export const CHANGED_MS = 1200;

function prefersReducedMotion() {
  return typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

// Fingerprint of the SCALAR/rows/sketch leaves reachable from `nodes` (kind + path, in order)
// plus, for "rows" leaves, the row count in `data` -- exactly what would force a rebuild.
export function structureSignature(nodes, data) {
  const parts = [];
  const walk = (list) => {
    for (const node of list) {
      if (node.kind === "group") {
        walk(node.children);
      } else if (node.kind === "rows") {
        const rows = readPath(data, node.path);
        parts.push(`rows:${node.path}:${Array.isArray(rows) ? rows.length : 0}`);
      } else {
        parts.push(`${node.kind}:${node.path}`);
      }
    }
  };
  walk(nodes);
  return parts.join("|");
}

// Exported: also used to diff HIGHLIGHTED scalars (results.js), which never appear in a `nodes`
// tree walk -- describeOutput hoists them out into the Sintesi before `diffScalarPaths` ever
// walks the tree, so a plain `===` at the call site would silently miss the NaN/NaN case this
// handles.
export function sameValue(a, b) {
  if (typeof a === "number" && typeof b === "number") return a === b || (Number.isNaN(a) && Number.isNaN(b));
  return a === b;
}

// Paths of SCALAR leaves whose value differs between the two data snapshots.
export function diffScalarPaths(nodes, previousData, nextData) {
  const changed = [];
  const walk = (list) => {
    for (const node of list) {
      if (node.kind === "group") walk(node.children);
      else if (node.kind === "scalar" && !sameValue(readPath(previousData, node.path), readPath(nextData, node.path))) {
        changed.push(node.path);
      }
    }
  };
  walk(nodes);
  return changed;
}

// Checks have no path (report.checks is a flat array): identified by `name`. Returns the set of
// names whose passed/value/detail changed, used to flash the corresponding Verifiche/eta-max rows.
export function diffChecks(previousChecks = [], nextChecks = []) {
  const before = new Map(previousChecks.map((check) => [check.name, check]));
  const changed = [];
  for (const check of nextChecks) {
    const prior = before.get(check.name);
    if (!prior || prior.passed !== check.passed || prior.value !== check.value || prior.detail !== check.detail) {
      changed.push(check.name);
    }
  }
  return changed;
}

// Marks `el` with `data-changed` for the marker-yellow fade (results.css); the whole feature is
// skipped under prefers-reduced-motion, not just animated instantly (spec: "none" under reduced
// motion, not "no animation but still flashes").
export function markChanged(el) {
  if (!el || prefersReducedMotion()) return;
  el.setAttribute("data-changed", "true");
  setTimeout(() => el.removeAttribute("data-changed"), CHANGED_MS);
}

// `scrollHost` is `#results-pane` (own-scroll column at >=1100px) or `window` as a fallback.
export function captureViewState(scrollHost) {
  const active = document.activeElement;
  const fieldRow = active && active.closest ? active.closest("[data-field]") : null;
  const groupToggle = active && active.classList && active.classList.contains("r-group-toggle") ? active : null;
  return {
    scrollTop: scrollHost === window ? window.scrollY : scrollHost ? scrollHost.scrollTop : 0,
    activeFieldPath: fieldRow ? fieldRow.dataset.field : null,
    activeGroupId: groupToggle ? groupToggle.id : null,
  };
}

export function restoreViewState(scrollHost, root, state) {
  if (scrollHost) {
    if (scrollHost === window) window.scrollTo(0, state.scrollTop);
    else scrollHost.scrollTop = state.scrollTop;
  }
  if (!root || !state) return;
  if (state.activeGroupId) {
    const target = root.querySelector(`#${CSS.escape(state.activeGroupId)}`);
    if (target) target.focus({ preventScroll: true });
    return;
  }
  if (state.activeFieldPath) {
    const target = root.querySelector(`[data-field="${CSS.escape(state.activeFieldPath)}"] .r-cell-value`);
    if (target) target.focus({ preventScroll: true });
  }
}
