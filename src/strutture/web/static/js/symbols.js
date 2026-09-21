// Builds mathematical-italic symbol markup with real <sub> elements from a plain-text hint
// such as "f_ck" or "V_Rd". Split at the FIRST "_"; the subscript stops at the first "(",
// space, or end of string, so trailing "(z)"/"(T)" stays on the baseline. Greek passes through
// as Unicode (rendered by the STIX/SymGreek stack set up in css/tokens.css).
//
// Orchestrator finding (design review 2026-09-21): "odd gap in the 'a g' subscript in form
// labels" -- a bare DocumentFragment used to flatten into whichever caller `.append()`ed it, so
// the base letter and its `<sub>` landed as SEPARATE direct children of the caller (e.g.
// `.f-field-label`, `display:flex; gap:var(--s1)`) and that flex `gap` opened up BETWEEN them,
// same as it would between any two unrelated items -- a subscript must sit tight against its own
// base letter regardless of what kind of container it is appended into. One wrapping `<span>`
// instead of a Fragment: every caller's plain `.append(symbolNode(...))`/`el(tag, {}, [symbolNode
// (...)])` pattern still works unchanged (both accept a single Node just as well as a Fragment),
// but the base+subscript+trailing now count as ONE flex/grid item wherever they land, so no
// container's own item spacing can ever reach between them.
export function symbolNode(symbol) {
  const wrap = document.createElement("span");
  wrap.className = "r-symbol";
  if (!symbol) return wrap;

  const underscoreIndex = symbol.indexOf("_");
  if (underscoreIndex === -1) {
    const base = document.createElement("i");
    base.className = "r-sym";
    base.textContent = symbol;
    wrap.append(base);
    return wrap;
  }

  const base = symbol.slice(0, underscoreIndex);
  const rest = symbol.slice(underscoreIndex + 1);
  const stop = rest.search(/[( ]/);
  const subEnd = stop === -1 ? rest.length : stop;
  const sub = rest.slice(0, subEnd);
  const trailing = rest.slice(subEnd);

  const baseEl = document.createElement("i");
  baseEl.className = "r-sym";
  baseEl.textContent = base;
  wrap.append(baseEl);

  if (sub) {
    const subEl = document.createElement("sub");
    subEl.textContent = sub;
    wrap.append(subEl);
  }

  if (trailing) {
    const tailEl = document.createElement("i");
    tailEl.className = "r-sym";
    tailEl.textContent = trailing;
    wrap.append(tailEl);
  }

  return wrap;
}

// Plain-text form for `title`/CSV headers -- the hint is already in this canonical notation.
export function symbolText(symbol) {
  return symbol ? symbol.trim() : "";
}

const SVG_NS = "http://www.w3.org/2000/svg";

// SVG counterpart of symbolNode: same "first `_`" tokenizer, but built from real <tspan>
// elements (SVG has no <sub>) so chart direct-labels render true subscripts instead of a
// same-baseline "T_C" string. Returns an array of <tspan> nodes to append to an SVG <text>.
export function symbolTspans(symbol) {
  const tspans = [];
  if (!symbol) return tspans;

  const underscoreIndex = symbol.indexOf("_");
  if (underscoreIndex === -1) {
    tspans.push(makeTspan(symbol));
    return tspans;
  }

  const base = symbol.slice(0, underscoreIndex);
  const rest = symbol.slice(underscoreIndex + 1);
  const stop = rest.search(/[( ]/);
  const subEnd = stop === -1 ? rest.length : stop;
  const sub = rest.slice(0, subEnd);
  const trailing = rest.slice(subEnd);

  tspans.push(makeTspan(base));
  if (sub) tspans.push(makeTspan(sub, { "baseline-shift": "sub", "font-size": "0.7em" }));
  if (trailing) tspans.push(makeTspan(trailing));
  return tspans;
}

function makeTspan(text, attrs = {}) {
  const node = document.createElementNS(SVG_NS, "tspan");
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  node.textContent = text;
  return node;
}

// Sketch dimension/arrow/diagram texts are produced by `etichetta_quota()` (sketch.py) as
// "simbolo = valore unità" ("l_s = 15,00 m") -- unlike `Etichetta.simbolo`, those shape kinds have
// no separate symbol field, so the whole string used to be printed as one raw run, subscript
// underscore and all. Matches a leading symbol token (letters/Greek, optional `_subscript`)
// followed by " = " and splits it off; `null` when the text is not in that form (an ordinary
// value/label strings through unchanged).
const SYMBOL_PREFIX_RE = /^([\p{L}][\p{L}\p{N}]*(?:_[\p{L}\p{N}]+)?)\s=\s(.+)$/u;

export function splitSymbolPrefix(text) {
  if (!text) return null;
  const match = SYMBOL_PREFIX_RE.exec(String(text));
  return match ? { symbol: match[1], rest: match[2] } : null;
}

// SVG tspans/text-node for a sketch text that MAY be in "simbolo = valore" form: the symbol runs
// through the same subscript tokenizer as `symbolTspans`, the rest (" = valore unità") stays a
// plain text node; ordinary text (no match) is a single text node, same as a raw `textContent`
// assignment. Used for `Quota.testo`, `Freccia.testo` and `Diagramma.etichette` -- every sketch
// text kind that carries its OWN symbol inline rather than in a separate `simbolo` field.
export function symbolAwareTspans(text) {
  if (!text) return [];
  const split = splitSymbolPrefix(text);
  if (!split) return [document.createTextNode(String(text))];
  return [...symbolTspans(split.symbol), document.createTextNode(` = ${split.rest}`)];
}
