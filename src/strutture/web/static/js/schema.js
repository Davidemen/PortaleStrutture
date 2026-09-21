// Resolves a pydantic-generated JSON input schema into a flat list of field descriptors.
// `advanced` comes ONLY from the backend `advanced` hint -- no hard-coded field-name list.
import { resolveProperty, hintsOf } from "./json-schema.js";

// A tuple/array is the table-input widget only when its items resolve to an object (§4b);
// a plain array of scalars (rare) falls back to the generic "text" rendering.
function isTableProperty(schema, property) {
  if (property.type !== "array") return false;
  const items = resolveProperty(schema, property.items || {});
  return items.type === "object" || Boolean(items.properties);
}

function fieldKind(schema, property) {
  if (isTableProperty(schema, property)) return "table";
  if (property.enum || property.const !== undefined) return "enum";
  if (property.type === "boolean") return "boolean";
  if (property.type === "integer" || property.type === "number") return "number";
  return "text";
}

function describeColumn(schema, name, rawProperty, required) {
  const property = resolveProperty(schema, rawProperty);
  const hints = hintsOf(property);
  return {
    name,
    kind: fieldKind(schema, property),
    label: property.description || property.title || name,
    unit: hints.unit ?? property.unit,
    symbol: hints.symbol ?? property.symbol,
    required: required.has(name),
    nullable: Boolean(property.nullable),
    enumValues: property.enum || (property.const !== undefined ? [property.const] : undefined),
    minimum: property.minimum,
    maximum: property.maximum,
    exclusiveMin: property.exclusiveMinimum,
    exclusiveMax: property.exclusiveMaximum,
    step: property.type === "integer" ? 1 : "any",
    aliases: property.aliases,
    unitOptions: property.unit_options,
  };
}

function describeTable(schema, property) {
  const itemsSchema = resolveProperty(schema, property.items || {});
  const itemsRequired = new Set(itemsSchema.required || []);
  const columns = Object.entries(itemsSchema.properties || {}).map(([name, raw]) =>
    describeColumn(schema, name, raw, itemsRequired),
  );
  const table = property.table || {};
  return {
    columns,
    table: {
      paste: table.paste !== false,
      csv: Boolean(table.csv),
      key: table.key,
      fixed_rows: Boolean(table.fixed_rows),
      preview_rows: table.preview_rows ?? 50,
    },
    minItems: property.minItems ?? 0,
    maxItems: property.maxItems,
  };
}

// `Field = {name, kind, label, help, unit, symbol, widget, group, advanced, condition, required,
//   nullable, default, enumValues, minimum, maximum, exclusiveMin, exclusiveMax, step,
//   columns?, table?, minItems?, maxItems?, unitSelector?, unitOptions?}` -- extends the §5 sketch
// with the table-input and unit-selector shape needed by the §4b addendum (see contractDeviations).
export function describeFields(schema) {
  const properties = schema.properties || {};
  const required = new Set(schema.required || []);
  const unitSelectorName = schema.unit_selector;
  return Object.entries(properties).map(([name, rawProperty]) => {
    const property = resolveProperty(schema, rawProperty);
    const hints = hintsOf(property);
    const kind = fieldKind(schema, property);
    const base = {
      name,
      kind,
      label: property.description || property.title || name,
      help: property.help,
      unit: hints.unit ?? property.unit,
      symbol: hints.symbol ?? property.symbol,
      widget: hints.widget ?? property.widget,
      group: hints.group ?? property.group,
      advanced: Boolean(hints.advanced ?? property.advanced),
      condition: hints.condition ?? property.condition,
      required: required.has(name),
      nullable: Boolean(property.nullable),
      default: property.default,
      enumValues: property.enum || (property.const !== undefined ? [property.const] : undefined),
      minimum: property.minimum,
      maximum: property.maximum,
      exclusiveMin: property.exclusiveMinimum,
      exclusiveMax: property.exclusiveMaximum,
      step: property.type === "integer" ? 1 : "any",
      unitSelector: unitSelectorName === name,
      unitOptions: property.unit_options,
    };
    return kind === "table" ? { ...base, ...describeTable(schema, property) } : base;
  });
}
