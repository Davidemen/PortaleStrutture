// AST JSON -> MathML Core (docs/architecture-phase2.md §3), built with `document.createElementNS`
// only -- never `innerHTML`. One exported function per equation LINE of a `Passo` (§5): the
// symbolic formula, the substitution, the result -- each returns either a `<math>` element (real
// rendering, MathML Core `mi`/`mn`/`mo`/`msub`/`msup`/`mfrac`/`msqrt`/`mrow`, fences for `par`/
// `abs`) or, when the browser cannot create MathML elements at all, a plain `<span>` carrying the
// SAME text `js/relazione-formule-testo.js` would have printed -- the graceful-degradation path
// the architecture brief requires. Every `<math>` also carries that plain text as `aria-label` AND
// `title` (accessible name + hover fallback, mirroring `testo.py`), so a screen reader or a browser
// with partial MathML support never has less information than the plain-text line would give.
import { el } from "./dom.js";
import {
  MENO,
  CIFRE_SIGNIFICATIVE_DEFAULT,
  CONFRONTI_TESTO,
  parseSimbolo,
  simboloIdentificatore,
  numeroLetteraleATesto,
  numeroACifreSignificative,
  valoreATesto,
  fattoreATesto,
  valoriDaPasso,
  formulaLineTesto,
  substitutionLineTesto,
  resultLineTesto,
  limiteDelConfronto,
} from "./relazione-formule-testo.js";

const MATHML_NS = "http://www.w3.org/1998/Math/MathML";
const OPERATORI_MATHML = { "+": "+", "-": MENO, "*": "·" };

// Feature detection (docs brief: "MathML must degrade gracefully if document.createElementNS math
// rendering is unsupported"). `MathMLElement` is the interface every MathML Core element inherits
// from in a browser that actually renders the tags below -- absent in one that would otherwise
// just show unstyled inline text with no visual structure at all.
export function mathSupported() {
  return typeof window !== "undefined" && "MathMLElement" in window;
}

function mnode(tag, children) {
  const node = document.createElementNS(MATHML_NS, tag);
  for (const child of children) node.append(child);
  return node;
}

function mleaf(tag, text) {
  const node = document.createElementNS(MATHML_NS, tag);
  node.textContent = text;
  return node;
}

const mrow = (children) => mnode("mrow", children);
const mo = (text) => mleaf("mo", text);
const mn = (text) => mleaf("mn", text);
const mi = (text) => mleaf("mi", text);

function buildIdentifierMathML({ base, sub }) {
  return sub ? mnode("msub", [mi(base), mi(sub)]) : mi(base);
}

// A substituted value: negative numbers print as "(−testo)", matching `valoreATesto`'s own
// parenthesisation rule for the plain-text line.
function buildValueMathML(valore, cifre) {
  if (valore < 0) return mrow([mo("("), mo(MENO), mn(numeroACifreSignificative(Math.abs(valore), cifre)), mo(")")]);
  return mn(numeroACifreSignificative(valore, cifre));
}

function buildNodeMathML(nodo, mode) {
  switch (nodo.t) {
    case "num":
      return mn(numeroLetteraleATesto(nodo));
    case "id":
      return mode.substitute
        ? buildValueMathML(mode.valori[simboloIdentificatore(nodo)], mode.cifre)
        : buildIdentifierMathML(nodo);
    case "neg":
      return mrow([mo(MENO), buildNodeMathML(nodo.a, mode)]);
    case "par":
      return mrow([mo("("), buildNodeMathML(nodo.a, mode), mo(")")]);
    case "fn":
      return _buildFunctionMathML(nodo, mode);
    case "op":
      return _buildOpMathML(nodo, mode);
    case "cmp":
      return mrow([buildNodeMathML(nodo.a, mode), mo(CONFRONTI_TESTO[nodo.op]), buildNodeMathML(nodo.b, mode)]);
    default:
      throw new Error(`nodo AST sconosciuto: ${nodo.t}`);
  }
}

function _buildOpMathML(nodo, mode) {
  // A fraction bar already groups its numerator and denominator: the source parentheses around a
  // whole operand ("A_s / (b * d)") are dropped here -- printed, they read "A_s over (b·d)", noise.
  if (nodo.op === "/") return mnode("mfrac", [buildNodeMathML(_senzaParentesi(nodo.a), mode), buildNodeMathML(_senzaParentesi(nodo.b), mode)]);
  if (nodo.op === "^") return mnode("msup", [buildNodeMathML(nodo.a, mode), buildNodeMathML(nodo.b, mode)]);
  return mrow([buildNodeMathML(nodo.a, mode), mo(OPERATORI_MATHML[nodo.op]), buildNodeMathML(nodo.b, mode)]);
}

function _senzaParentesi(nodo) {
  return nodo && nodo.t === "par" ? nodo.a : nodo;
}

function _buildFunctionMathML(nodo, mode) {
  if (nodo.name === "sqrt") return mnode("msqrt", [buildNodeMathML(nodo.args[0], mode)]);
  if (nodo.name === "abs") return mrow([mo("|"), buildNodeMathML(nodo.args[0], mode), mo("|")]);
  const children = [mi(nodo.name), mo("(")];
  nodo.args.forEach((arg, index) => {
    if (index > 0) children.push(mo(","));
    children.push(buildNodeMathML(arg, mode));
  });
  children.push(mo(")"));
  return mrow(children);
}

function _needsParensForFactor(nodo) {
  return nodo.t === "neg" || (nodo.t === "op" && (nodo.op === "+" || nodo.op === "-"));
}

function _buildFactorMathML(scala) {
  const esponente = Math.round(_log10Sicuro(scala));
  if (Math.abs(scala - 10 ** esponente) <= 1e-12 * Math.abs(scala)) {
    return mnode("msup", [mn("10"), mn(String(esponente).replace("-", MENO))]);
  }
  return mn(valoreATesto(scala));
}

function _log10Sicuro(valore) {
  return valore > 0 ? Math.log10(valore) : 0.5;
}

// Mirrors `relazione-formule-testo.js::applyFactorTesto`, structurally on the AST: parenthesises a
// sum/difference/unary-minus operand before appending "·10⁻³"; a comparison carries the factor on
// its left operand only.
function buildWithFactorMathML(nodo, mode, scala) {
  const fattore = fattoreATesto(scala);
  if (!fattore) return buildNodeMathML(nodo, mode);
  if (nodo.t === "cmp") {
    const sinistra = buildWithFactorMathML(nodo.a, mode, scala);
    return mrow([sinistra, mo(CONFRONTI_TESTO[nodo.op]), buildNodeMathML(nodo.b, mode)]);
  }
  const base = _needsParensForFactor(nodo) ? mrow([mo("("), buildNodeMathML(nodo, mode), mo(")")]) : buildNodeMathML(nodo, mode);
  return mrow([base, mo("·"), _buildFactorMathML(scala)]);
}

// Builds the `<math>` element for `mathmlFn()`, or the plain-text fallback `<span>` when MathML is
// unsupported; `testo` becomes the accessible name (+ `title`) either way.
function finalizeLine(testo, mathmlFn) {
  if (!mathSupported()) return el("span", { class: "r-eq-fallback", text: testo });
  const math = document.createElementNS(MATHML_NS, "math");
  // Display style: full-size fractions. Inline style (the default) sets every numerator and
  // denominator in script size -- in a calculation report the fractions ARE the content.
  math.setAttribute("displaystyle", "true");
  math.append(mathmlFn());
  math.setAttribute("aria-label", testo);
  math.setAttribute("title", testo);
  return math;
}

// Line 1 of §5: "simbolo = formula" (with the display factor folded in when `passo.scala !== 1`).
export function buildFormulaLine(passo) {
  const ast = passo.formula_ast;
  const testo = formulaLineTesto(passo, ast);
  return finalizeLine(testo, () =>
    mrow([buildIdentifierMathML(parseSimbolo(passo.simbolo)), mo("="), buildWithFactorMathML(ast, { substitute: false }, passo.scala)]),
  );
}

// Line 2: the same AST with every identifier replaced by its formatted value.
export function buildSubstitutionLine(passo) {
  const ast = passo.formula_ast;
  const testo = substitutionLineTesto(passo, ast);
  const mode = { substitute: true, valori: valoriDaPasso(passo), cifre: CIFRE_SIGNIFICATIVE_DEFAULT };
  return finalizeLine(testo, () => mrow([mo("="), buildWithFactorMathML(ast, mode, passo.scala)]));
}

// Line 3: "= risultato" (+ unit, appended by the caller as plain text) or, for a check step,
// "= risultato op limite" -- the esito icon/word is also the caller's job (js/relazione-sviluppo.js),
// not part of the equation itself.
export function buildResultLine(passo) {
  const ast = passo.formula_ast;
  const testo = resultLineTesto(passo, ast);
  return finalizeLine(testo, () => {
    if (!passo.esito) return mrow([mo("="), buildValueMathML(passo.risultato, CIFRE_SIGNIFICATIVE_DEFAULT)]);
    const limite = limiteDelConfronto(passo, ast);
    return mrow([
      mo("="),
      buildValueMathML(passo.risultato, CIFRE_SIGNIFICATIVE_DEFAULT),
      mo(CONFRONTI_TESTO[ast.op]),
      buildValueMathML(limite, CIFRE_SIGNIFICATIVE_DEFAULT),
    ]);
  });
}
