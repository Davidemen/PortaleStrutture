// Pure-function unit tests for js/relazione-formule-testo.js (docs/architecture-phase2.md §3/§5):
// the plain-text/number rendering that mirrors `strutture.shared.relazione.testo`, plus the
// minimal AST evaluator used for a check step's printed limit. No DOM, no server, no Playwright:
//   node --test tests/e2e/relazione_formule_testo.test.mjs
//
// The `ca-taglio-non-armato` fixtures below (`F_CK`, `RHO_L`, `V_RD1`) are the EXACT `Passo`
// objects `strutture.shared.tool.execute(TOOL, TOOL.example, con_relazione=True)` produces (dumped
// with `Passo.model_dump(mode="json")` + `ast_a_json(analizza(passo.formula))`), and the expected
// strings below were captured from `strutture.shared.relazione.testo.passo_a_testo` on that SAME
// run -- this is a byte-for-byte parity check against the Python text renderer, not a hand-typed
// approximation of it. New module: only in static_next (staging) so far, not yet promoted to the
// live static/ copy.
import test from "node:test";
import assert from "node:assert/strict";
import {
  MENO,
  parseSimbolo,
  simboloIdentificatore,
  numeroLetteraleATesto,
  numeroACifreSignificative,
  valoreATesto,
  fattoreATesto,
  renderNodoTesto,
  applyFactorTesto,
  formulaLineTesto,
  substitutionLineTesto,
  resultLineTesto,
  limiteDelConfronto,
  valutaAst,
} from "../../src/strutture/web/static/js/relazione-formule-testo.js";

// -- fixtures: real `Passo` objects from ca-taglio-non-armato's own `relazione.py` --------------

const F_CK = {
  simbolo: "f_ck",
  formula: "0.83 * R_ck",
  valori: [{ simbolo: "R_ck", valore: 35.0, unita: "MPa", descrizione: "resistenza cubica caratteristica" }],
  risultato: 29.049999999999997,
  unita: "MPa",
  clausola: "NTC2018 §11.2.10.1",
  esito: "",
  scala: 1.0,
  formula_ast: { t: "op", op: "*", a: { t: "num", v: 0.83 }, b: { t: "id", base: "R", sub: "ck" } },
};

const RHO_L = {
  simbolo: "ρ_l",
  formula: "A_sl / (b_w * d) <= 0.02",
  valori: [
    { simbolo: "A_sl", valore: 1005.0, unita: "mm2", descrizione: "" },
    { simbolo: "b_w", valore: 1000.0, unita: "mm", descrizione: "" },
    { simbolo: "d", valore: 450.0, unita: "mm", descrizione: "" },
  ],
  risultato: 0.0022333333333333333,
  unita: "-",
  clausola: "NTC2018 §4.1.2.3.5.1",
  esito: "soddisfatta",
  scala: 1.0,
  formula_ast: {
    t: "cmp",
    op: "<=",
    a: {
      t: "op", op: "/",
      a: { t: "id", base: "A", sub: "sl" },
      b: { t: "par", a: { t: "op", op: "*", a: { t: "id", base: "b", sub: "w" }, b: { t: "id", base: "d", sub: "" } } },
    },
    b: { t: "num", v: 0.02 },
  },
};

const V_RD1 = {
  simbolo: "V_Rd,1",
  formula: "(0.18 * k * (100 * ρ_l * f_ck)^(1/3) / γ_c + 0.15 * σ_cp) * b_w * d",
  valori: [
    { simbolo: "k", valore: 1.6666666666666665, unita: "", descrizione: "" },
    { simbolo: "ρ_l", valore: 0.0022333333333333333, unita: "", descrizione: "rapporto di armatura, già limitato a ρl,max" },
    { simbolo: "f_ck", valore: 29.049999999999997, unita: "MPa", descrizione: "" },
    { simbolo: "γ_c", valore: 1.5, unita: "", descrizione: "" },
    { simbolo: "σ_cp", valore: 0.0, unita: "MPa", descrizione: "" },
    { simbolo: "b_w", valore: 1000.0, unita: "mm", descrizione: "" },
    { simbolo: "d", valore: 450.0, unita: "mm", descrizione: "" },
  ],
  risultato: 167.8581391736332,
  unita: "kN",
  clausola: "NTC2018 §4.1.2.3.5.1",
  esito: "",
  scala: 0.001,
  // Verbatim `ast_a_json(analizza(V_RD1.formula))` (docs/architecture-phase2.md §3 wire format).
  formula_ast: {
    t: "op", op: "*",
    a: {
      t: "op", op: "*",
      a: {
        t: "par",
        a: {
          t: "op", op: "+",
          a: {
            t: "op", op: "/",
            a: {
              t: "op", op: "*",
              a: { t: "op", op: "*", a: { t: "num", v: 0.18 }, b: { t: "id", base: "k", sub: "" } },
              b: {
                t: "op", op: "^",
                a: { t: "par", a: { t: "op", op: "*", a: { t: "op", op: "*", a: { t: "num", v: 100.0 }, b: { t: "id", base: "ρ", sub: "l" } }, b: { t: "id", base: "f", sub: "ck" } } },
                b: { t: "par", a: { t: "op", op: "/", a: { t: "num", v: 1.0 }, b: { t: "num", v: 3.0 } } },
              },
            },
            b: { t: "id", base: "γ", sub: "c" },
          },
          b: { t: "op", op: "*", a: { t: "num", v: 0.15 }, b: { t: "id", base: "σ", sub: "cp" } },
        },
      },
      b: { t: "id", base: "b", sub: "w" },
    },
    b: { t: "id", base: "d", sub: "" },
  },
};

// -- numeri / testo --------------------------------------------------------------------------

test("numeroLetteraleATesto keeps the literal source number, comma decimal", () => {
  assert.equal(numeroLetteraleATesto({ v: 0.83 }), "0,83");
  assert.equal(numeroLetteraleATesto({ v: 1000 }), "1000");
  assert.equal(numeroLetteraleATesto({ v: 0.02 }), "0,02");
});

test("numeroACifreSignificative rounds to 4 significant digits and strips trailing zeros", () => {
  assert.equal(numeroACifreSignificative(29.049999999999997), "29,05");
  assert.equal(numeroACifreSignificative(1.6666666666666665), "1,667");
  assert.equal(numeroACifreSignificative(0.405895500600102), "0,4059");
  assert.equal(numeroACifreSignificative(0.0022333333333333333), "0,002233");
  assert.equal(numeroACifreSignificative(1000), "1000");
  assert.equal(numeroACifreSignificative(500), "500");
  assert.equal(numeroACifreSignificative(0), "0");
});

test("valoreATesto parenthesises negative values with U+2212", () => {
  assert.equal(valoreATesto(12.3), "12,3");
  assert.equal(valoreATesto(-12.3), `(${MENO}12,3)`);
  assert.equal(valoreATesto(0), "0");
});

test("fattoreATesto prints a power of ten as a superscript, nothing for scala=1", () => {
  assert.equal(fattoreATesto(1), "");
  assert.equal(fattoreATesto(0.001), "10⁻³");
  assert.equal(fattoreATesto(1_000_000), "10⁶");
});

test("fattoreATesto falls back to a plain formatted number for a non-power-of-ten factor", () => {
  assert.equal(fattoreATesto(2.5), "2,5");
});

test("parseSimbolo/simboloIdentificatore split at the first underscore only", () => {
  assert.deepEqual(parseSimbolo("V_Rd,1"), { base: "V", sub: "Rd,1" });
  assert.deepEqual(parseSimbolo("d"), { base: "d", sub: "" });
  assert.equal(simboloIdentificatore(parseSimbolo("V_Rd,1")), "V_Rd,1");
  assert.equal(simboloIdentificatore(parseSimbolo("d")), "d");
});

// -- rendering an AST, symbolic and substituted -----------------------------------------------

test("renderNodoTesto renders sqrt/min/max/abs as plain calls, never a radical glyph", () => {
  const sqrtNode = { t: "fn", name: "sqrt", args: [{ t: "op", op: "/", a: { t: "num", v: 200 }, b: { t: "id", base: "d", sub: "" } }] };
  assert.equal(renderNodoTesto(sqrtNode, { substitute: false }), "sqrt(200 / d)");
  const absNode = { t: "fn", name: "abs", args: [{ t: "id", base: "x", sub: "" }] };
  assert.equal(renderNodoTesto(absNode, { substitute: false }), "|x|");
});

test("applyFactorTesto puts the factor on the comparison's LEFT operand only", () => {
  const cmp = {
    t: "cmp", op: "<=",
    a: { t: "op", op: "/", a: { t: "id", base: "a", sub: "" }, b: { t: "id", base: "b", sub: "" } },
    b: { t: "num", v: 100 },
  };
  const testo = applyFactorTesto(cmp, { substitute: false }, 0.001);
  assert.equal(testo, "a / b·10⁻³ ≤ 100");
});

test("applyFactorTesto parenthesises a sum/difference operand before the factor", () => {
  const sum = { t: "op", op: "+", a: { t: "id", base: "a", sub: "" }, b: { t: "id", base: "b", sub: "" } };
  assert.equal(applyFactorTesto(sum, { substitute: false }, 0.001), "(a + b)·10⁻³");
  const product = { t: "op", op: "*", a: { t: "id", base: "a", sub: "" }, b: { t: "id", base: "b", sub: "" } };
  assert.equal(applyFactorTesto(product, { substitute: false }, 0.001), "a·b·10⁻³");
});

// -- the three lines of a Passo, against the REAL Python-rendered text --------------------------

test("formulaLineTesto: f_ck (no factor, no clause in the text)", () => {
  assert.equal(formulaLineTesto(F_CK, F_CK.formula_ast), "f_ck = 0,83·R_ck");
});

test("substitutionLineTesto/resultLineTesto: f_ck", () => {
  assert.equal(substitutionLineTesto(F_CK, F_CK.formula_ast), "= 0,83·35");
  assert.equal(resultLineTesto(F_CK, F_CK.formula_ast), "= 29,05 MPa");
});

test("formulaLineTesto/substitutionLineTesto: ρ_l (comparison, Par kept from the source)", () => {
  assert.equal(formulaLineTesto(RHO_L, RHO_L.formula_ast), "ρ_l = A_sl / (b_w·d) ≤ 0,02");
  assert.equal(substitutionLineTesto(RHO_L, RHO_L.formula_ast), "= 1005 / (1000·450) ≤ 0,02");
});

test("resultLineTesto: a check step shows risultato, limite and esito", () => {
  assert.equal(resultLineTesto(RHO_L, RHO_L.formula_ast), "= 0,002233 ≤ 0,02  (soddisfatta)");
});

test("limiteDelConfronto evaluates the comparison's right operand", () => {
  assert.equal(limiteDelConfronto(RHO_L, RHO_L.formula_ast), 0.02);
});

test("V_Rd,1: display factor 10⁻³ on the outer product, both formula and substitution lines", () => {
  assert.equal(
    formulaLineTesto(V_RD1, V_RD1.formula_ast),
    "V_Rd,1 = (0,18·k·(100·ρ_l·f_ck)^(1 / 3) / γ_c + 0,15·σ_cp)·b_w·d·10⁻³",
  );
  assert.equal(
    substitutionLineTesto(V_RD1, V_RD1.formula_ast),
    "= (0,18·1,667·(100·0,002233·29,05)^(1 / 3) / 1,5 + 0,15·0)·1000·450·10⁻³",
  );
  assert.equal(resultLineTesto(V_RD1, V_RD1.formula_ast), "= 167,9 kN");
});

// -- valutaAst: min/max/sqrt/degrees -------------------------------------------------------------

test("valutaAst evaluates arithmetic, min/max and sqrt", () => {
  const ast = { t: "fn", name: "min", args: [{ t: "num", v: 3 }, { t: "op", op: "+", a: { t: "num", v: 1 }, b: { t: "num", v: 1 } }] };
  assert.equal(valutaAst(ast, {}), 2);
  const sqrtAst = { t: "fn", name: "sqrt", args: [{ t: "num", v: 16 }] };
  assert.equal(valutaAst(sqrtAst, {}), 4);
});

test("valutaAst looks up identifiers from `valori`, raises on an unknown one", () => {
  const ast = { t: "op", op: "*", a: { t: "id", base: "x", sub: "" }, b: { t: "num", v: 2 } };
  assert.equal(valutaAst(ast, { x: 5 }), 10);
  assert.throws(() => valutaAst(ast, {}));
});

test("valutaAst takes sin/cos/tan/atan in degrees only when the argument's own unit is °", () => {
  const angleId = { t: "id", base: "θ", sub: "" };
  const sinAst = { t: "fn", name: "sin", args: [angleId] };
  const inDegrees = valutaAst(sinAst, { θ: 90 }, { θ: "°" });
  assert.ok(Math.abs(inDegrees - 1) < 1e-12, `sin(90°) should be 1, got ${inDegrees}`);
  const inRadians = valutaAst(sinAst, { θ: 90 }, {});
  assert.ok(Math.abs(inRadians - Math.sin(90)) < 1e-12, "no unit hint -> radians, same as Math.sin");
});

test("large and tiny values keep the significant digits in positional notation (mirrors testo.py)", async () => {
  const { numeroACifreSignificative } = await import("../../src/strutture/web/static/js/relazione-formule-testo.js");
  assert.equal(numeroACifreSignificative(3859521.926595), "3860000");
  assert.equal(numeroACifreSignificative(125000), "125000");
  assert.equal(numeroACifreSignificative(0.000123456), "0,0001235");
  assert.equal(numeroACifreSignificative(182.7345), "182,7");
});
