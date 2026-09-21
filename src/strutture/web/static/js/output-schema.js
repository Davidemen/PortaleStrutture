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

// A `Check` field (pass/fail against a code clause) is structurally `{name: str, passed: bool, ...}`.
// It is never rendered as a scalar/group in the results tree -- the same information is already
// surfaced once, flat, via `report.checks` (the Sintesi + the synthesised "Verifiche" group), so
// rendering it again here would both duplicate it and print raw "[object Object]" (format.js has
// no notion of a Check value).
function isCheckSchema(resolved) {
  const required = resolved.required || [];
  const props = resolved.properties || {};
  return (
    resolved.type === "object" &&
    required.includes("name") &&
    required.includes("passed") &&
    props.passed &&
    props.passed.type === "boolean"
  );
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
  const columnEntries = Object.entries(itemsResolved.properties || {})
    .map(([colName, rawCol]) => [colName, resolveProperty(root, rawCol)])
    .filter(([, colResolved]) => !isCheckSchema(colResolved));
  const columns = columnEntries.map(([colName, colResolved]) => describeScalar(root, colName, `${path}.${colName}`, colResolved));
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

// The `widget: "sketch"` hint (backend contract: src/strutture/shared/sketch.py) marks an output
// field holding a `Sketch | None`. It becomes its own leaf kind -- never a "group" (a `Sketch` is
// `type: object` and would otherwise match `isGroupSchema`) -- so the Sintesi can pull it out with
// `extractByPredicate` and the generic group renderer never sees it (requirement: no raw-JSON group).
function describeSketch(root, name, path, resolved) {
  return { kind: "sketch", name, path, label: labelFor(name, resolved.description) };
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
  return Object.entries(properties)
    .map(([name, raw]) => {
      const resolved = resolveProperty(root, raw);
      const path = basePath ? `${basePath}.${name}` : name;
      const hints = hintsOf(resolved);
      if (hints.widget === "sketch") return describeSketch(root, name, path, resolved);
      if (isCheckSchema(resolved)) return null;
      if (isRowsSchema(resolved)) return describeRows(root, name, path, resolved);
      if (isGroupSchema(resolved)) return describeGroup(root, name, path, resolved);
      return describeScalar(root, name, path, resolved);
    })
    .filter((node) => node !== null);
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
    if ((node.kind === "scalar" || node.kind === "rows" || node.kind === "sketch") && predicate(node)) {
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

// The collapsible group header preview (WORKBENCH_SPEC #4): the first `limit` DIRECT scalar
// children that have a value, as `{node, value}` pairs -- nested groups/rows are never pulled in
// (a preview is a hint of what's inside, not a second copy of it).
export function groupPreviewPairs(node, data, limit = 2) {
  const pairs = [];
  for (const child of node.children || []) {
    if (pairs.length >= limit) break;
    if (child.kind !== "scalar") continue;
    const value = readPath(data, child.path);
    if (value === null || value === undefined) continue;
    pairs.push({ node: child, value });
  }
  return pairs;
}

// A `rows` node's individual COLUMNS can carry `highlight` too (real example: muro-sostegno's
// `ribaltamento_scorrimento[].or_ribaltamento`/`os_scorrimento` -- a per-combination safety
// factor, not a top-level scalar). There is no single value to hoist the way a scalar highlight
// works, so the Sintesi figure shown for such a column is its WORST value across every row -- the
// smallest safety factor is the governing one, the same "smaller is worse" convention
// `verdict.js`'s utilisation already assumes. Additive, not exclusive: the full table still shows
// every row (unlike a plain scalar highlight, hoisting only two of a table's N columns out of it
// would leave a confusingly incomplete table behind).
export function rowsHighlightPairs(nodes, data) {
  const pairs = [];
  const walk = (list) => {
    for (const node of list) {
      if (node.kind === "group") {
        walk(node.children);
        continue;
      }
      if (node.kind !== "rows") continue;
      const rows = readPath(data, node.path) || [];
      for (const column of node.columns) {
        if (!column.highlight) continue;
        const values = rows.map((row) => row[column.name]).filter((v) => typeof v === "number" && !Number.isNaN(v));
        if (values.length === 0) continue;
        pairs.push({
          node: { ...column, path: `${node.path}[].${column.name}` },
          value: Math.min(...values),
        });
      }
    }
  };
  walk(nodes);
  return pairs;
}

// The tool's FIRST `rows` node carrying a `chart` hint, wherever nested inside a group -- design
// review 2026-09-21, orchestrator finding: a tool with no checks, no `highlight` outputs and no
// sketch (e.g. sisma-spettro, vento-pressione) used to render a visibly EMPTY Sintesi block; when
// it has a chart, that is shown there instead of nothing.
export function firstChartNode(nodes) {
  for (const node of nodes) {
    if (node.kind === "rows" && node.chart) return node;
    if (node.kind === "group") {
      const found = firstChartNode(node.children);
      if (found) return found;
    }
  }
  return null;
}

// True when `node` (a "group") has at least one descendant scalar/rows with a non-null value --
// used to decide whether an otherwise-empty group should be rendered at all.
export function groupHasContent(node, data) {
  for (const child of node.children || []) {
    if (child.kind === "scalar" || child.kind === "sketch") {
      if (readPath(data, child.path) !== null && readPath(data, child.path) !== undefined) return true;
    } else if (child.kind === "rows") {
      const rows = readPath(data, child.path);
      if (Array.isArray(rows) && rows.length > 0) return true;
    } else if (child.kind === "group") {
      if (groupHasContent(child, data)) return true;
    }
  }
  return false;
}
