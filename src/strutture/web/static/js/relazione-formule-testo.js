// PURE (no DOM) AST -> plain-text rendering + minimal evaluation for "Sviluppo dei calcoli"
// (docs/architecture-phase2.md §2/§3/§5). Mirrors, deliberately field-by-field,
// `strutture.shared.relazione.testo` (decimal comma, "·" for `*`, U+2212 minus, "≤ ≥" for
// comparisons, negative substituted values parenthesised, the "·10⁻³" display factor) and the
// small subset of `strutture.shared.relazione.valuta` needed to print a check step's numeric
// limit -- so the browser's plain-text fallback/accessible-name always agrees with what the
// Python text renderer would have printed for the SAME `Passo`. No DOM API is used anywhere in
// this file: every function here is unit-testable with `node --test`.
// AST JSON shape (ast_json.py): {"t":"num","v"} | {"t":"id","base","sub"} | {"t":"neg","a"} |
// {"t":"par","a"} | {"t":"op","op","a","b"} | {"t":"fn","name","args"} | {"t":"cmp","op","a","b"}.
import { toSuperscript } from "./format.js";

export const MENO = "−"; // U+2212 MINUS SIGN, not the ASCII hyphen -- matches testo.py's MENO
export const CIFRE_SIGNIFICATIVE_DEFAULT = 4;

export const CONFRONTI_TESTO = { "<=": "≤", ">=": "≥", "<": "<", ">": ">", "=": "=" };
const OPERATORI_TESTO = { "+": " + ", "-": ` ${MENO} `, "*": "·", "/": " / ", "^": "^" };

// "V_Rd,1" -> {base:"V", sub:"Rd,1"}; "d" -> {base:"d", sub:""} -- the SAME "split at the first
// underscore" rule as `notazione.py::_scomponi_identificatore` (Greek ASCII names are already
// normalised server-side by the time a `Passo.simbolo`/AST `id` reaches the browser, so no
// alpha/gamma/... translation is needed here).
export function parseSimbolo(testo) {
  const indice = testo.indexOf("_");
  if (indice === -1) return { base: testo, sub: "" };
  return { base: testo.slice(0, indice), sub: testo.slice(indice + 1) };
}

// The `valori`/`unita` lookup key for an `id` AST node OR a `parseSimbolo()` result: `base` alone,
// or `base_sub` when there is a subscript -- mirrors `notazione.py::simbolo_identificatore`.
export function simboloIdentificatore({ base, sub }) {
  return sub ? `${base}_${sub}` : base;
}

// {symbol -> value} / {symbol -> unita} straight off `Passo.valori` -- shared by the substitution
// text/MathML and by `limiteDelConfronto` below.
export function valoriDaPasso(passo) {
  return Object.fromEntries(passo.valori.map((valore) => [valore.simbolo, valore.valore]));
}

export function unitaDaPasso(passo) {
  return Object.fromEntries(passo.valori.filter((valore) => valore.unita).map((valore) => [valore.simbolo, valore.unita]));
}

// Mirrors `testo.py::_numero_letterale_a_testo`: the literal source number as written in the
// notation ("0.4" -> "0,4"), never evaluated/rounded -- used for `num` AST nodes in BOTH the
// symbolic and the substitution line (only `id` nodes differ between the two).
export function numeroLetteraleATesto(nodo) {
  return String(nodo.v).replace(".", ",");
}

// Mirrors `testo.py::_numero_a_cifre_significative`: always `cifre` significant digits in plain
// positional notation, never "e" and never the float's own digits -- 3859521,93 -> "3860000",
// 0,000123456 -> "0,0001235" (a proof-read finding: a surface printed with twelve digits reads as a
// typesetting error in a signed report). `valore` is always non-negative (the sign is handled by
// `valoreATesto`, one level up).
export function numeroACifreSignificative(valore, cifre = CIFRE_SIGNIFICATIVE_DEFAULT) {
  if (valore === 0) return "0";
  const esponente = Math.floor(Math.log10(valore) + 1e-9);
  const posizione = cifre - 1 - esponente; // decimals to keep; negative = round to tens/hundreds/...
  const fattore = 10 ** posizione;
  const arrotondato = Math.round(valore * fattore) / fattore;
  const grezzo = arrotondato.toFixed(Math.max(0, posizione));
  const senzaZeriInutili = grezzo.includes(".") ? grezzo.replace(/0+$/, "").replace(/\.$/, "") : grezzo;
  return senzaZeriInutili.replace(".", ",");
}

// Mirrors `testo.py::valore_a_testo`: Italian-formatted number, negative values parenthesised
// ("(−12,3)") -- used for every substituted identifier and for the result line's own value(s).
export function valoreATesto(valore, cifre = CIFRE_SIGNIFICATIVE_DEFAULT) {
  const testo = numeroACifreSignificative(Math.abs(valore), cifre);
  return valore < 0 ? `(${MENO}${testo})` : testo;
}

// Mirrors `testo.py::fattore_a_testo`: "" when `scala` is 1 (nothing printed), "10⁻³" for a power
// of ten (unit conversion, e.g. Nmm -> kNm), the plain formatted number otherwise.
export function fattoreATesto(scala) {
  if (scala === 1) return "";
  const esponente = Math.round(_log10Sicuro(scala));
  if (Math.abs(scala - 10 ** esponente) <= 1e-12 * Math.abs(scala)) {
    return `10${toSuperscript(esponente)}`;
  }
  return valoreATesto(scala);
}

function _log10Sicuro(valore) {
  return valore > 0 ? Math.log10(valore) : 0.5; // a non-positive factor is never a power of ten
}

// Mirrors `testo.py::_rendi` (the generic AST -> text walk): `mode = {substitute, valori?, cifre?}`
// -- `substitute: false` renders an `id` node as its symbol ("R_ck"), `substitute: true` as its
// formatted value from `mode.valori` (`sostituzione_a_testo`). Numbers are ALWAYS the literal
// source text regardless of `mode`, matching testo.py's `_rendi` call sites for both variants.
export function renderNodoTesto(nodo, mode) {
  switch (nodo.t) {
    case "num":
      return numeroLetteraleATesto(nodo);
    case "id":
      return mode.substitute
        ? valoreATesto(mode.valori[simboloIdentificatore(nodo)], mode.cifre)
        : simboloIdentificatore(nodo);
    case "neg":
      return `${MENO}${renderNodoTesto(nodo.a, mode)}`;
    case "par":
      return `(${renderNodoTesto(nodo.a, mode)})`;
    case "fn":
      return _renderFunzioneTesto(nodo, mode);
    case "op":
      return `${renderNodoTesto(nodo.a, mode)}${OPERATORI_TESTO[nodo.op]}${renderNodoTesto(nodo.b, mode)}`;
    case "cmp":
      return `${renderNodoTesto(nodo.a, mode)} ${CONFRONTI_TESTO[nodo.op]} ${renderNodoTesto(nodo.b, mode)}`;
    default:
      throw new Error(`nodo AST sconosciuto: ${nodo.t}`);
  }
}

// Mirrors `testo.py::_rendi_funzione`: only `abs` gets its own "|x|" glyph in PLAIN TEXT -- `sqrt`
// and every other function print as an ordinary call ("sqrt(200 / d)"), same as testo.py (the
// MathML radical is a `js/relazione-formule.js`-only affordance, the browser's OWN rendering,
// not something the text fallback needs to reproduce).
function _renderFunzioneTesto(nodo, mode) {
  const testi = nodo.args.map((arg) => renderNodoTesto(arg, mode));
  if (nodo.name === "abs") return `|${testi[0]}|`;
  return `${nodo.name}(${testi.join(", ")})`;
}

// Mirrors `testo.py::_con_fattore`: "espressione·10⁻³" -- a sum/difference/unary-minus operand is
// parenthesised first; a comparison carries the factor on its LEFT operand only (that is what
// `Passo.risultato` is). Recurses on the AST directly (rather than Python's string-partition) so
// it never depends on the comparison glyph being absent from either operand's OWN rendered text.
export function applyFactorTesto(nodo, mode, scala) {
  const fattore = fattoreATesto(scala);
  if (!fattore) return renderNodoTesto(nodo, mode);
  if (nodo.t === "cmp") {
    const sinistra = applyFactorTesto(nodo.a, mode, scala);
    return `${sinistra} ${CONFRONTI_TESTO[nodo.op]} ${renderNodoTesto(nodo.b, mode)}`;
  }
  const espressione = renderNodoTesto(nodo, mode);
  const serveParentesi = nodo.t === "neg" || (nodo.t === "op" && (nodo.op === "+" || nodo.op === "-"));
  return serveParentesi ? `(${espressione})·${fattore}` : `${espressione}·${fattore}`;
}

// The three lines of `testo.py::passo_a_testo` (§5), minus the clause -- `js/relazione-sviluppo.js`
// prints `clausola` as its OWN, separately-readable DOM node (right-aligned, muted ink) rather
// than appending it to the accessible name/title text a second time.
export function formulaLineTesto(passo, ast) {
  return `${passo.simbolo} = ${applyFactorTesto(ast, { substitute: false }, passo.scala)}`;
}

export function substitutionLineTesto(passo, ast) {
  const mode = { substitute: true, valori: valoriDaPasso(passo), cifre: CIFRE_SIGNIFICATIVE_DEFAULT };
  return `= ${applyFactorTesto(ast, mode, passo.scala)}`;
}

export function resultLineTesto(passo, ast) {
  if (!passo.esito) {
    const unita = passo.unita && passo.unita !== "-" ? ` ${passo.unita}` : "";
    return `= ${valoreATesto(passo.risultato)}${unita}`;
  }
  const limite = limiteDelConfronto(passo, ast);
  return `= ${valoreATesto(passo.risultato)} ${CONFRONTI_TESTO[ast.op]} ${valoreATesto(limite)}  (${passo.esito})`;
}

// `Passo.risultato` is only ever the LEFT operand of a check's comparison (docs/architecture-
// phase2.md §1) -- the right-hand limit ("≤ 1", "≤ 0,02", ...) has to be EVALUATED from `ast.b`,
// mirroring `testo.py::_riga_risultato`'s own call to `valuta.valuta`.
export function limiteDelConfronto(passo, ast) {
  return valutaAst(ast.b, valoriDaPasso(passo), unitaDaPasso(passo));
}

// --- minimal evaluator (subset of strutture.shared.relazione.valuta, browser-side) -------------
// Only ever called on a check's RIGHT operand above: never used to validate `risultato` itself
// (that drift check is the Python harness's job, docs/architecture-phase2.md §4).
const GRADO = "°";
const TRIGONOMETRICHE = new Set(["sin", "cos", "tan", "atan"]);
const FUNZIONI_UN_ARGOMENTO = {
  sqrt: Math.sqrt, abs: Math.abs, sin: Math.sin, cos: Math.cos, tan: Math.tan,
  atan: Math.atan, exp: Math.exp, ln: Math.log, log10: Math.log10,
};
const OPERATORI_VALUTA = {
  "+": (a, b) => a + b, "-": (a, b) => a - b, "*": (a, b) => a * b, "/": (a, b) => a / b, "^": (a, b) => a ** b,
};
const CONFRONTI_VALUTA = {
  "<=": (a, b) => a <= b, ">=": (a, b) => a >= b, "<": (a, b) => a < b, ">": (a, b) => a > b, "=": (a, b) => a === b,
};

export function valutaAst(nodo, valori, unita = {}) {
  switch (nodo.t) {
    case "num":
      return nodo.v;
    case "id": {
      const simbolo = simboloIdentificatore(nodo);
      if (!(simbolo in valori)) throw new Error(`identificatore sconosciuto: ${simbolo}`);
      return valori[simbolo];
    }
    case "neg":
      return -valutaAst(nodo.a, valori, unita);
    case "par":
      return valutaAst(nodo.a, valori, unita);
    case "op":
      return OPERATORI_VALUTA[nodo.op](valutaAst(nodo.a, valori, unita), valutaAst(nodo.b, valori, unita));
    case "cmp":
      return CONFRONTI_VALUTA[nodo.op](valutaAst(nodo.a, valori, unita), valutaAst(nodo.b, valori, unita));
    case "fn":
      return _valutaFunzione(nodo, valori, unita);
    default:
      throw new Error(`nodo AST sconosciuto: ${nodo.t}`);
  }
}

function _valutaFunzione(nodo, valori, unita) {
  const argomenti = nodo.args.map((arg) => valutaAst(arg, valori, unita));
  if (nodo.name === "min") return Math.min(...argomenti);
  if (nodo.name === "max") return Math.max(...argomenti);
  let [valore] = argomenti;
  if (TRIGONOMETRICHE.has(nodo.name) && _argomentoInGradi(nodo.args[0], unita)) valore = (valore * Math.PI) / 180;
  return FUNZIONI_UN_ARGOMENTO[nodo.name](valore);
}

function _argomentoInGradi(argomento, unita) {
  return argomento.t === "id" && unita[simboloIdentificatore(argomento)] === GRADO;
}
