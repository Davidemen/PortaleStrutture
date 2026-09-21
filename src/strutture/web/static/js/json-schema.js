// Shared JSON-schema helpers -- resolves pydantic-generated schemas and reads
// the backend hint contract (DESIGN_SPEC.md #4). Owned by the shell package;
// forms/results import this instead of duplicating resolution logic.

const HINT_KEYS = [
  "unit",
  "widget",
  "group",
  "advanced",
  "condition",
  "symbol",
  "highlight",
  "legacy_only",
  "chart",
];

export function resolveRef(root, ref) {
  const path = ref.replace(/^#\//, "").split("/");
  return path.reduce((node, key) => (node ? node[key] : undefined), root);
}

export function resolveProperty(root, raw) {
  if (raw && raw.$ref) {
    const target = resolveRef(root, raw.$ref) || {};
    const { $ref, ...rest } = raw;
    return { ...target, ...rest };
  }
  if (raw && Array.isArray(raw.anyOf)) {
    const nonNull = raw.anyOf.find((option) => option.type !== "null") || raw.anyOf[0] || {};
    const nullable = raw.anyOf.some((option) => option.type === "null");
    const resolvedOption = resolveProperty(root, nonNull);
    const { anyOf, ...rest } = raw;
    return { ...resolvedOption, ...rest, nullable };
  }
  return raw || {};
}

export function hintsOf(prop) {
  const source = prop || {};
  return HINT_KEYS.reduce((acc, key) => ({ ...acc, [key]: source[key] }), {});
}
