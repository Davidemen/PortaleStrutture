// Resolves an OUTPUT json-schema into a tree of render-ready Node descriptors for the results
// sheet. No per-tool code: everything here is driven purely by the schema + hints.
import { resolveProperty, hintsOf } from "./json-schema.js";

// Backend model/field descriptions sometimes carry a leading spreadsheet reference for
// traceability, e.g. "`CX25:DA27` -- inviluppo di armatura minima ...". Strip that prefix and
// any stray backticks before a description is ever shown as a label or group title.
const REF_PREFIX = /^(?:`[^`]{1,80}`[,\s]*)+[-–—:]\s*/;

export function cleanText(raw) {
  if (!raw) return "";
  const withoutPrefix = raw.trim().replace(REF_PREFIX, "");
  const withoutTicks = withoutPrefix.replace(/`([^`]*)`/g, "$1");
  return withoutTicks.replace(/\s+/g, " ").trim();
}

export function humanize(name) {
  const spaced = name.replace(/_/g, " ").trim();
  return spaced.length > 0 ? spaced.charAt(0).toUpperCase() + spaced.slice(1) : name;
}

function labelFor(name, description) {
  return cleanText(description) || humanize(name);
}

function isRowsSchema(resolved) {
  return resolved.type === "array" && Boolean(resolved.items);
}

function isGroupSchema(resolved) {
  return resolved.type === "object" && Boolean(resolved.properties) && resolved.enum === undefined;
}

function describeScalar(root, name, path, resolved) {
  const hints = hintsOf(resolved);
  return {
    kind: "scalar",
    name,
    path,
    label: labelFor(name, resolved.description),
    symbol: hints.symbol,
    unit: hints.unit,
    highlight: Boolean(hints.highlight),
    legacyOnly: Boolean(hints.legacy_only),
    integer: resolved.type === "integer",
  };
}

function describeRows(root, name, path, resolved) {
  const hints = hintsOf(resolved);
  const itemsResolved = resolveProperty(root, resolved.items);
  const columnEntries = Object.entries(itemsResolved.properties || {});
  const columns = columnEntries.map(([colName, rawCol]) =>
    describeScalar(root, colName, `${path}.${colName}`, resolveProperty(root, rawCol))
  );
  return {
    kind: "rows",
    name,
    path,
    label: labelFor(name, resolved.description),
    highlight: Boolean(hints.highlight),
    legacyOnly: Boolean(hints.legacy_only),
    chart: hints.chart,
    rowsPage: typeof resolved.rows_page === "number" ? resolved.rows_page : undefined,
    columns,
  };
}

function describeGroup(root, name, path, resolved) {
  const hints = hintsOf(resolved);
  return {
    kind: "group",
    name,
    path,
    label: labelFor(name, resolved.description),
    highlight: Boolean(hints.highlight),
    legacyOnly: Boolean(hints.legacy_only),
    children: describeProperties(root, resolved, path),
  };
}

function describeProperties(root, objectSchema, basePath) {
  const properties = objectSchema.properties || {};
  return Object.entries(properties).map(([name, raw]) => {
    const resolved = resolveProperty(root, raw);
    const path = basePath ? `${basePath}.${name}` : name;
    if (isRowsSchema(resolved)) return describeRows(root, name, path, resolved);
    if (isGroupSchema(resolved)) return describeGroup(root, name, path, resolved);
    return describeScalar(root, name, path, resolved);
  });
}

// Top-level entry point: outputSchema is the `output` member of GET /api/tools/{name}/schema.
export function describeOutput(outputSchema) {
  if (!outputSchema || !outputSchema.properties) return [];
  return describeProperties(outputSchema, outputSchema, "");
}

// Recursively pulls every scalar/rows node matching `predicate` out of the tree, wherever it is
// nested, and returns the remainder with now-empty groups dropped. Reused for both the
// highlight hoist and the legacy_only split.
export function extractByPredicate(nodes, predicate) {
  const matched = [];
  const rest = [];
  for (const node of nodes) {
    if ((node.kind === "scalar" || node.kind === "rows") && predicate(node)) {
      matched.push(node);
      continue;
    }
    if (node.kind === "group") {
      const inner = extractByPredicate(node.children, predicate);
      matched.push(...inner.matched);
      if (inner.rest.length > 0) rest.push({ ...node, children: inner.rest });
      continue;
    }
    rest.push(node);
  }
  return { matched, rest };
}

export function readPath(data, path) {
  if (data === null || data === undefined) return undefined;
  return path.split(".").reduce((acc, key) => (acc === null || acc === undefined ? undefined : acc[key]), data);
}
