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
  const base = `#/${encodeURIComponent(tool)}`;
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

function notify() {
  const route = readRoute();
  for (const callback of listeners) {
    callback(route);
  }
}

export function start() {
  window.addEventListener("hashchange", notify);
  window.addEventListener("popstate", notify);
  notify();
}
