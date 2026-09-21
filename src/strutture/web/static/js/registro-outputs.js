// Resolves a register entry's `uscite` (output paths) to a human label via the FIRST affected
// tool's own output schema -- WORKBENCH_SPEC §13.1: "the outputs affected (label from the tool's
// output schema when resolvable, else the path)". Schemas are fetched once per tool and cached: a
// registro page can list entries for every tool in the app, and only the rows an engineer actually
// expands ever need one.
import { fetchSchema } from "./api.js";
import { describeOutput, indexScalarPaths } from "./output-schema.js";

const cache = new Map(); // toolName -> Promise<Map<path, node>>

function pathIndexFor(toolName) {
  if (!cache.has(toolName)) {
    cache.set(
      toolName,
      fetchSchema(toolName)
        .then((schema) => indexScalarPaths(describeOutput(schema.output)))
        .catch(() => new Map())
    );
  }
  return cache.get(toolName);
}

// -> [{path, label, symbol, unit}], one per `uscite` entry, in order.
export async function resolveOutputLabels(strumenti, uscite) {
  if (!uscite || uscite.length === 0) return [];
  const toolName = strumenti && strumenti[0];
  const index = toolName ? await pathIndexFor(toolName) : new Map();
  return uscite.map((path) => {
    const node = index.get(path);
    return node ? { path, label: node.label, symbol: node.symbol, unit: node.unit } : { path, label: path };
  });
}
