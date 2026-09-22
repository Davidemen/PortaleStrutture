// Hash routing -- DESIGN_SPEC.md #2. Format: #/<tool-name>?<field>=<value>&...
// start() must be called before first paint so a cold deep link renders the
// tool without an extra click.

const listeners = new Set();

export function readRoute() {
  const hash = window.location.hash || "";
  const withoutHash = hash.startsWith("#") ? hash.slice(1) : hash;
  const withoutSlash = withoutHash.startsWith("/") ? withoutHash.slice(1) : withoutHash;
  const [toolPart, queryPart] = withoutSlash.split("?");
  const tool = toolPart ? decodeURIComponent(toolPart) : null;
  const params = {};
  if (queryPart) {
    for (const pair of queryPart.split("&")) {
      if (!pair) continue;
      const [rawKey, rawValue = ""] = pair.split("=");
      if (!rawKey) continue;
      params[decodeURIComponent(rawKey)] = decodeURIComponent(rawValue.replace(/\+/g, " "));
    }
  }
  return { tool, params };
}

function buildHash(tool, params) {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join("&");
  // `tool` is occasionally a multi-segment path (WORKBENCH_SPEC §14.2/§14.3: "progetti/<id>") --
  // each segment is escaped on its own so the "/" stays a real path separator in the address bar
  // (readRoute()'s own decodeURIComponent(toolPart) already tolerates either form, so this is
  // purely cosmetic, but "#/progetti%2F<id>" would be a confusing URL to see/share).
  const path = String(tool).split("/").map(encodeURIComponent).join("/");
  const base = `#/${path}`;
  return query ? `${base}?${query}` : base;
}

export function navigate(tool, params = {}, { replace = false } = {}) {
  const hash = buildHash(tool, params);
  if (replace) {
    const url = `${window.location.pathname}${window.location.search}${hash}`;
    window.history.replaceState(null, "", url);
  } else {
    window.location.hash = hash;
  }
}

export function onRoute(callback) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

// Observed (Chromium): clicking a same-page `<a href="#/...">` fires BOTH "hashchange" and
// "popstate" for the ONE logical navigation -- `start()` below listens to both (the second is
// still needed for real back/forward traversal), so without this a single click used to call
// every `onRoute` listener TWICE in a row. Most pages tolerate that fine (a plain, synchronous
// `clear(root)` + rebuild just repaints from scratch, harmlessly), but it is a real bug for
// anything that awaits BEFORE its first paint finishes (js/progetto.js's own `renderProgetto`: an
// async `fetchProgetto` between the top-of-function `clear(root)` and its later `root.append(...)`
// let a stale first call's append land AFTER a second call's, doubling the whole page).
//
// Coalesced via a same-tick `setTimeout(…, 0)`, NOT a "skip if same as the last route dispatched"
// flag: an earlier version of this fix remembered the last route and skipped a repeat, but two
// genuinely separate, fast, round-trip navigations (observed under Playwright: create a project,
// `navigate()` to it, then immediately `page.goto()` back to the list -- each a separate CDP
// command, not one click) can land back on the SAME route the dispatcher had already recorded
// before either of their OWN event handlers ever got a chance to run, permanently "stuck" thinking
// nothing had changed and never re-rendering the list at all. Coalescing by TIMING instead has no
// such memory: any calls to `notify()` within one tick collapse into a single dispatch of
// whatever `readRoute()` returns when that tick's timer fires, and every later, genuinely separate
// navigation still gets its own full dispatch.
let notifyTimer = null;

function notify() {
  if (notifyTimer !== null) return;
  notifyTimer = setTimeout(() => {
    notifyTimer = null;
    const route = readRoute();
    for (const callback of listeners) {
      callback(route);
    }
  }, 0);
}

export function start() {
  window.addEventListener("hashchange", notify);
  window.addEventListener("popstate", notify);
  notify();
}
