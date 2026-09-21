# Phase 2 architecture — relazione di calcolo with formulas

Goal: the printed report shows, for the results that matter, what an engineer writes by hand:

    M_Rd = A_s · f_yd · (d − 0,4 · x)                      NTC2018 §4.1.2.3.4.2
         = 1570 · 391,3 · (450 − 0,4 · 98,2)
         = 252,3 kNm
    η = M_Ed / M_Rd = 214,0 / 252,3 = 0,85 ≤ 1             soddisfatta

Follow `docs/BUILD_CONTRACT.md` (modularity, frozen models, TDD, Windows + macOS).

## 0. The decision: a VERIFIED RESTATEMENT, not instrumentation
The calculation code is not touched and no number can change. Each adopting tool gets a separate pure function
`relazione(inputs, output) -> tuple[Traccia, ...]` that restates its formulas in a small notation and picks the
values from the inputs and the already-computed output (it may call the package's own step functions for an
intermediate the output does not expose). Drift between the displayed formula and the code is caught by a test
harness (§4): every step's notation is PARSED and EVALUATED with the step's own values and must reproduce the
step's result. Rejected alternatives: operator-overloading number types (invasive, slow, touches every formula),
formula strings without evaluation (they rot silently).
Cost model: the trace is built only on request (`relazione=1`), never during live calculation.

## 1. Package `strutture.shared.relazione` (pure, no FastAPI)
| module | content |
|---|---|
| `modelli.py` | frozen pydantic models below |
| `notazione.py` | tokenizer + Pratt parser: notation string -> AST (frozen dataclasses); `NotazioneError` with position |
| `valuta.py` | `valuta(ast, valori: Mapping[str, float]) -> float \| bool`; unknown identifier -> `NotazioneError` |
| `testo.py` | AST -> plain text with Italian typography ("A_s·f_yd·(d − 0,4·x)") for title attributes / future DOCX |
| `ast_json.py` | AST -> JSON-able dict (§3), the ONLY form sent to the browser |
| `verifica.py` | `problemi_traccia(tracce) -> tuple[str, ...]` used by the harness and by a debug assertion in tests |

```python
class Valore(BaseModel):          # frozen
    simbolo: str                  # "f_yd" — same notation as the UI `symbol` hint
    valore: float
    unita: str = ""
    descrizione: str = ""         # Italian, optional ("tensione di snervamento di progetto")

class Passo(BaseModel):           # frozen — one displayed equation
    simbolo: str                  # left-hand side, "M_Rd"; for a check: the utilisation symbol, "η"
    formula: str                  # notation (§2): "A_s * f_yd * (d - 0.4 * x)"; a check: "M_Ed / M_Rd <= 1"
    valori: tuple[Valore, ...]    # every identifier of `formula`, in order of first appearance
    risultato: float              # value of the left-hand side (for a check: of the left operand)
    unita: str = ""
    clausola: str = ""            # "NTC2018 §4.1.2.3.4.2"; REQUIRED for check steps
    nota: str = ""                # Italian, one sentence, optional
    esito: Literal["", "soddisfatta", "non soddisfatta"] = ""   # non-empty iff `formula` is a comparison
    scala: float = 1.0            # display factor result = scala * eval (unit conversion, e.g. 1e-6 for Nmm -> kNm)

class Traccia(BaseModel):         # frozen — one section of "Sviluppo dei calcoli"
    titolo: str                   # Italian, "Resistenza a flessione"
    passi: tuple[Passo, ...]      # 1..40
```
`Report` gains `relazione: tuple[Traccia, ...] = ()` (on the envelope — NO output model changes). `Tool` gains
`relazione: Callable[[Input, Output], tuple[Traccia, ...]] | None = None`. `execute(tool, raw, *, con_relazione=False)`:
when asked and the run is ok, calls it inside the same try/except discipline — a failing trace NEVER fails the
calculation: the report carries the warning "Sviluppo dei calcoli non disponibile per questi dati." and an empty
`relazione`. Excel mode (`legacy_compat=True`): `relazione` stays empty with the warning "Lo sviluppo dei calcoli
descrive la modalità standard: non è disponibile in modalità Excel." (legacy branches compute different formulas).
API: `POST /api/tools/{name}/run?relazione=1`. `GET /api/tools` and `/schema` expose `relazione: bool`.

## 2. Notation (one grammar, three consumers: evaluator, text, browser)
- numbers: `450`, `0.4`, `1e-3` (decimal POINT in the source; shown with a comma);
- identifiers: letter (Latin or Greek, Unicode allowed: `σ`, `η`, `φ`) + letters/digits, optional subscript after the
  first `_` which may contain letters, digits, `,` and `'` — `A_s`, `M_Rd,x`, `σ_c,max`, `c'_k`, `f_yd`; ASCII Greek
  names are accepted and normalised (`alpha` -> `α`, `gamma_c` -> `γ_c`, `phi'_k` -> `φ'_k`);
- operators by precedence: `^` (right-assoc) > unary `-` > `*` `/` > `+` `-` > comparisons `<=` `>=` `<` `>` `=`
  (at most ONE comparison, at top level); multiplication is always explicit (`*`, shown as `·`);
- grouping `( )`, absolute value `abs(x)` (shown `|x|`);
- functions: `sqrt`, `min`, `max`, `abs`, `sin`, `cos`, `tan`, `atan`, `exp`, `ln`, `log10`; trigonometric functions
  take DEGREES when the argument's identifier has unit "°" in `valori`, radians otherwise — the evaluator receives the
  units map for exactly this purpose (document it; test both).
No assignment, no strings, no attribute access, no calls other than the list above: the parser is a whitelist.

## 3. AST JSON (the wire format) and browser rendering
`{"t":"num","v":0.4}` · `{"t":"id","base":"M","sub":"Rd,x"}` · `{"t":"op","op":"*","a":…,"b":…}` (`+ - * / ^`) ·
`{"t":"neg","a":…}` · `{"t":"par","a":…}` (source parentheses are kept) · `{"t":"fn","name":"sqrt","args":[…]}` ·
`{"t":"cmp","op":"<=","a":…,"b":…}`. Each `Passo` is sent with `formula_ast` next to the raw `formula`.
Browser (`js/relazione-formule.js`, DOM only — `document.createElementNS`, never `innerHTML`): AST -> MathML Core
(`mi`, `mn`, `mo`, `msub`, `msup`, `mfrac` for `/`, `msqrt`, `mrow`, fences for `par`/`abs`). The SUBSTITUTION line
is the same AST with every `id` replaced by its formatted value (format.js, Italian decimals, 4 significant digits;
negative values parenthesised). Font: self-hosted STIX Two Math (woff2) for `math`; fallback: `testo.py`'s string in
a `title` and as the accessible name. No CDN, CSP unchanged.

## 4. The harness (the reason this design is safe)
`tests/shared/relazione/harness.py::assert_relazione_coerente(tool, raw_inputs)`: runs `execute(..., con_relazione=
True)` and for EVERY `Passo` asserts: the formula parses; its identifiers == the symbols in `valori` (no missing, no
unused); `scala * valuta(formula) ≈ risultato` (rel 1e-6, abs 1e-9); for a comparison, the boolean matches `esito`
and `clausola` is non-empty; `unita` is present whenever the matching output field has a unit hint; every
`risultato` that corresponds to an output field (same symbol hint) equals that output value. A parametrised test
runs it for every tool that declares `relazione`, on its example AND on each golden-case input of that package.
A second global test: every `highlight` output of an adopting tool appears as a `Passo.simbolo` somewhere (the
numbers on the first page of the report are always explained).

## 5. Report and overlay (extends WORKBENCH_SPEC §10–§11)
Document order gains "Sviluppo dei calcoli" AFTER "Verifiche": one block per `Traccia` (title), one equation group
per `Passo`: line 1 `simbolo = formula` with the clause right-aligned in muted ink; line 2 `= substitution`; line 3
`= risultato unità` (check: `= 0,85 ≤ 1` + esito as icon + word). `break-inside: avoid` per Passo. Many-rows tools
trace the GOVERNING row only and say so in the Traccia title ("… — combinazione governante SLU 12"). Overlay option
"Sviluppo dei calcoli" (default ON when the tool offers it; hidden otherwise). The print builder requests a FRESH
run with `relazione=1` for the current valid inputs (report rule: stale results are never exported).

## 6. Adoption order and size
Core first (one builder: §1–§4 + API + a demo adoption on `ca-taglio-non-armato`, the smallest real tool). Then UI
(one builder: §3 browser + §5). Then adoption in waves of disjoint packages, each = `relazione.py` (+ tests through
the harness, nothing else): wave 1 `ca_travi`, `ca_punzonamento`, `plinti_isolati`; wave 2 `ca_pilastri`, `muro`,
`plinti_pali`; wave 3 loads (neve, vento, sisma) and the rest. Target per tool: 8–25 steps covering every check
and every highlight. Review: one Opus engineering pass per wave reading ONLY the rendered text of the traces
(`testo.py`) against the norm clauses — formulas an engineer would sign.
