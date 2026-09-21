// Builds mathematical-italic symbol markup with real <sub> elements from a plain-text hint
// such as "f_ck" or "V_Rd". Split at the FIRST "_"; the subscript stops at the first "(",
// space, or end of string, so trailing "(z)"/"(T)" stays on the baseline. Greek passes through
// as Unicode (rendered by the STIX/SymGreek stack set up in css/tokens.css).
export function symbolNode(symbol) {
  const fragment = document.createDocumentFragment();
  if (!symbol) return fragment;

  const underscoreIndex = symbol.indexOf("_");
  if (underscoreIndex === -1) {
    const base = document.createElement("i");
    base.className = "r-sym";
    base.textContent = symbol;
    fragment.append(base);
    return fragment;
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
  fragment.append(baseEl);

  if (sub) {
    const subEl = document.createElement("sub");
    subEl.textContent = sub;
    fragment.append(subEl);
  }

  if (trailing) {
    const tailEl = document.createElement("i");
    tailEl.className = "r-sym";
    tailEl.textContent = trailing;
    fragment.append(tailEl);
  }

  return fragment;
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
