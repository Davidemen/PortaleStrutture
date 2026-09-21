# Neve (Snow Load) — Implementation Spec

Source workbook `neve.xlsx`, sheets: `Neve`, `Neve accumulo`, `Tabelle`, `Comuni`.
Governing code: DM 17/01/2018 §3.4 (Neve), §C3.4.5.6 circolare (accumulo neve su coperture adiacenti a costruzioni più alte) ≈ EN 1991-1-3 Annex B.3.

## Comuni sheet (shared lookup, diverges from sisma/vento workbooks)

`Comuni!A:J`, 8101 data rows (row2..8102), columns: A Regione, B Provincia, C Codice Istat, D Comune (lookup key), E Sismica zone, F Vento zone, G Neve zone, I=`=B` (Provincia dup), J=`=A` (Regione dup).

Diff vs `sisma.xlsx`/`vento.xlsx` Comuni CSVs (same row order/Comune list, same E "Sismica" column — 0 diffs):
- Column F "Vento" differs in 377/8101 rows.
- Column G "Neve" differs in 495/8101 rows.
- sisma.xlsx and vento.xlsx Comuni sheets are byte-identical to each other; neve.xlsx carries its own (newer or otherwise inconsistent) snapshot for Vento/Neve zone assignment on ~5-6% of comuni. Sismic zone data is consistent across all three workbooks.
- Consequence: a "vento" tool relying on `Comuni!F` from the vento workbook may disagree with what `neve.xlsx` would report for the same comune. Downstream architect should treat each workbook's Comuni as authoritative only for its own unit, or reconcile the two Vento columns explicitly.

## Tool 1: `neve-carico-falda` — snow load on single/double-pitch roof

### Purpose
Computes ground snow load qsk (§3.4.2), exposure coeff CE (§3.4.3), thermal coeff Ct (§3.4.4), shape coeff μ (§3.4.5, NTC 2018 Table 3.4.II / EN1991-1-3 Table 5.2) and design roof snow load qs = qsk·CE·Ct·μ for a 1- or 2-pitch roof. Sheet `Neve`.

### Inputs
| cell | symbol | meaning | unit | type | example |
|---|---|---|---|---|---|
| H5 | comune | Comune name | - | text, must exist in Comuni!D | "Mapello" |
| H9 | as | Altitude a.s.l. | m | number ≥0 | 250 |
| H13 | topografia | Exposure class | - | enum: Battuta dai venti / Normale / Riparata | "Normale" |
| H26 | Ct | Thermal coefficient | - | number, default 1 | 1 |
| G29 | tipo_copertura | Roof type selector (display only, see bug §7) | - | enum: "Copertura ad una falda" / "Copertura a due falde" | "Copertura ad una falda" |
| H30 | a | Pitch angle (single-pitch case) | ° | number 0-90 | 0 |
| H31 | parapetto | Barrier at lower eave? (single-pitch) | - | enum SI/NO | "NO" |
| H52 | a1 | Pitch 1 angle (two-pitch case) | ° | number | 35 |
| H53 | parapetto1 | Barrier, pitch1 | - | enum SI/NO | "NO" |
| H56 | a2 | Pitch 2 angle (two-pitch case) | ° | number | 50 |
| H57 | parapetto2 | Barrier, pitch2 | - | enum SI/NO | "NO" |

### Outputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| H6 | provincia | derived | - | "Bergamo" |
| H7 | regione | derived | - | "Lombardia" |
| H8 | zona | Macrozona neve | - | "I (alpina)" |
| H10 | qsk | Ground snow load | kN/m2 | 1.55392 |
| H14 | CE | Exposure coefficient | - | 1 |
| H32 | μ (single pitch) | Shape coefficient | - | 0.8 |
| D34 | qs (single pitch) | Design roof snow load | kN/m2 | 1.24314 |
| H54 | μ1 (pitch1) | Shape coefficient | - | 0.666667 |
| H58 | μ2 (pitch2) | Shape coefficient | - | 0.266667 |
| D60 | qs (pitch1) | Design roof snow load | kN/m2 | 1.03595 |
| H61 | qs (pitch2) | Design roof snow load | kN/m2 | 0.414379 |

### Calculation steps
1. `provincia[H6] = VLOOKUP(comune[H5], Comuni!D:J, col6="I", exact)`.
2. `regione[H7] = VLOOKUP(comune[H5], Comuni!D:J, col7="J", exact)`.
3. `zona[H8] = VLOOKUP(comune[H5], Comuni!D:J, col4="G", exact)` → one of "I (alpina)", "I (mediterranea))" [sic, extra paren, see §7], "II", "III".
4. `qsk[H10] = as[H9]<200 ? LOOKUP(zona, Tabelle.qsk1) : LOOKUP(zona, Tabelle.qsk2(as))` — table row selected by nearest-lower/approx match (VLOOKUP TRUE range lookup) on `zona`. See Tabelle below.
5. `CE[H14] = LOOKUP(topografia[H13], ExposureTable)` exact match; table rows: "Battuta dai venti"→0.9, "Normale"→1, "Riparata"→1.1.
6. Shape coefficient, single pitch: `μ[H32] = parapetto[H31]="SI" ? 0.8 : (a[H30]<30 ? 0.8 : (30<a<60 ? 0.8·(60-a)/30 : 0))`. (a≥60 → 0; a=30 or a=60 exactly fall through the strict `AND(>30,<60)` to the else branch → 0, see §7.)
7. `qs[D34] = qsk[H10]·CE[H14]·Ct[H26]·μ[H32]`.
8. Pitch1: `μ1[H54]` same formula as step 6 using `parapetto1[H53]`, `a1[H52]`. `qs1[D60] = qsk·CE·Ct·μ1`.
9. Pitch2: `μ2[H58]` same formula using `parapetto2[H57]`, `a2[H56]`. `qs2[H61] = qsk·CE·Ct·μ2`.
10. `G29` selector and note cell `K30` are informational only — they do not gate which of D34 vs D60/H61 is the "active" output; both branches are always computed (see §7).

### Lookup tables
- `Tabelle!A3:C6` key=Zona (A): row "I (alpina)" → qsk1[B]=1.5, qsk2[C]=`1.39·(1+(as/728)²)`; "I (mediterranea))" → qsk1=1.5, qsk2=`1.35·(1+(as/602)²)`; "II" → qsk1=1, qsk2=`0.85·(1+(as/481)²)`; "III" → qsk1=0.6, qsk2=`0.51·(1+(as/481)²)`. VLOOKUP uses range(TRUE) lookup but `zona` is text — behaves as exact match only if the 4 rows are pre-sorted; not literally an interpolation. **All C3:C6 formulas hardcode `Neve!$H$9`** regardless of which sheet calls the table (see §7, Bug 1).
- `Neve!A16:I20` (ExposureTable) key=Topografia (A), value=col I (9th of range): exact match.
- `Comuni!D:J`: key=Comune (D), exact match; cols returned by relative offset (6→I=Provincia, 7→J=Regione, 4→G=Neve zona).

### Constants
- qsk1 base values {1.5, 1.5, 1.0, 0.6} kN/m2 and qsk2 formula coefficients {1.39/728, 1.35/602, 0.85/481, 0.51/481} — NTC 2018 Table 3.4.I zonal values.
- CE {0.9, 1.0, 1.1} — NTC 2018 Table 3.4.I.
- μ breakpoints 30°, 60°, base 0.8 — NTC 2018 Table 3.4.II / EN 1991-1-3 Table 5.2 / NTC Fig 3.4.2 (roof-shape coefficient), 0-30°→0.8, 30-60°→linear to 0, ≥60°→0.

## Tool 2: `neve-accumulo` — drift load near taller adjacent building

### Purpose
§C3.4.5.6 (circolare NTC): additional/redistributed snow load on a lower roof abutting a taller building, from wind redistribution (μw) and sliding off the upper roof (μs). Sheet `Neve accumulo`.

### Inputs
| cell | symbol | meaning | unit | type | example |
|---|---|---|---|---|---|
| H5 | comune | Comune name | - | text | "Bergamo" |
| H9 | as | Altitude a.s.l. | m | number | 249 |
| H13 | topografia | Exposure class | - | enum (same as tool 1) | "Normale" |
| H26 | Ct | Thermal coefficient | - | number | 1 |
| H29 | b1 | Width of taller building | m | number>0 | 43.15 |
| H30 | b2 | Width of lower building | m | number>0 | 36.2 |
| H31 | h | Height difference at drift zone | m | number>0 | 10 |
| H32 | γ | Snow specific weight (code-recommended 2) | kN/m2(equiv.) | number | 2 |
| H34 | a | Pitch angle of taller building's roof | ° | number | 0 |
| H35 | m1 | Shape coeff, lower flat roof (manual input, may be overridden, see step 9) | - | number | 0.8 |
| H37 | msup | Shape coeff of upper roof slope (fixed input) | - | number | 0.45 |

### Outputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| H8 | zona | Macrozona neve | - | "I (alpina)" |
| H10 | qsk | Ground snow load | kN/m2 | 1.5 |
| H14 | CE | Exposure coefficient | - | 1 |
| H33 | ls | Drift-zone length | m | 15 |
| H36 | mw | Wind-redistribution shape coeff | - | 3.9675 |
| H38 | ms | Sliding shape coeff | - | 0 |
| H39 | m2 | Total shape coeff at wall | - | 3.9675 |
| H43 | m1_final | Design shape coeff, far edge | - | 0.8 |
| H44 | m2_final | Design shape coeff, near wall | - | 3.9675 |
| H45 | ls_final | Design drift length | m | 15 |

Design roof loads are `qsk·CE·Ct·m1_final` and `qsk·CE·Ct·m2_final` (not built into the sheet as separate cells — apply NTC eq. 3.4.1 manually with H43/H44).

### Calculation steps
1. `provincia[H6]/regione[H7]` same VLOOKUP pattern as tool 1, keyed on `H5`.
2. `zona[H8] = VLOOKUP(provincia[H6], Comuni!D:J, 4, exact)` — **keyed on H6 (Provincia), not H5 (Comune)** (see §7, Bug 2).
3. `qsk[H10] = as[H9]<200 ? LOOKUP(zona,Tabelle.qsk2(as)) : LOOKUP(zona,Tabelle.qsk1)` — **branches swapped vs tool 1** (see §7, Bug 3). Tabelle.qsk2 column still evaluates using `Neve!H9` (tool-1 sheet's altitude), not this sheet's `H9` (Bug 1).
4. `CE[H14]` = same ExposureTable lookup as tool 1 (local copy `A16:I20` on this sheet).
5. `ls[H33] = clamp(2·h[H31], 5, 15)` m.
6. `γh_over_qsk[K32] = γ[H32]·h[H31]/qsk[H10]`.
7. `μw_raw[K35] = MIN((b1[H29]+b2[H30])/(2·h[H31]), K32)`.
8. `mw[H36] = K35<4 ? (K35>0.8 ? K35 : 0.8) : 4` — clamps μw ∈ [0.8, 4] ("4" cap — verify against EC1 Annex B, code commonly cites 4 as γh/qsk cap? — confidence: ?).
9. `ms[H38] = a[H34]<15 ? 0 : msup[H37]/2`.
10. `slope_per_m[K38] = (mw[H36]-m1[H35])/ls[H33]`.
11. `extrap_at_b2[L38] = slope_per_m·(ls[H33]-b2[H30])`.
12. `m1_interp[M38] = extrap_at_b2 + m1[H35]`.
13. `m2[H39] = ms[H38] + mw[H36]`.
14. `m1_final[H43] = b2[H30] < ls[H33] ? m1_interp[M38] : m1[H35]` (per note: "Se b2<ls il valore di m1 è ottenuto per interpolazione lineare").
15. `m2_final[H44] = m2[H39]`.
16. `ls_final[H45] = ls[H33]`.

### Lookup tables
Same `Tabelle!A3:C6` and local `A16:I20` ExposureTable as tool 1 (exact-match on zona/topografia respectively).

### Constants
- γ recommended 2 kN/m2 (snow bulk density for drift calc, §C3.4.5.6).
- ls bounds [5,15] m — EN1991-1-3 Annex B.3 (ls = 2h, clamped 5≤ls≤15).
- mw bounds [0.8,4] — cap value "4" unverified against source clause (marked "?").
- ms threshold a<15° → 0 — sliding contribution ignored below 15° pitch (EC1 Annex B.3 convention).

## Suspected bugs / fragile spots (all re-verified against formulas above)

1. **Cross-sheet contamination in `Tabelle!C3:C6`**: all four qsk2 formulas hardcode `Neve!$H$9`, so `Neve accumulo`'s qsk computation silently uses `Neve` sheet's altitude input instead of its own `H9` whenever the qsk2 branch is selected. Confirmed by reading `Tabelle!C3`..`C6` — every one references `Neve!$H$9`, none reference `'Neve accumulo'!H9`.
2. **`Neve accumulo!H8` keyed on Provincia, not Comune**: `VLOOKUP(H6, Comuni!D:J, 4, FALSE)` looks up the *Provincia* string (H6) inside `Comuni!D`, which is the *Comune* column. Only works by coincidence when Provincia name equals a Comune name (true for the golden case "Bergamo"/"Bergamo"); for most towns this VLOOKUP will `#N/A` or hit the wrong comune. Tool 1's equivalent cell `Neve!H8` correctly uses `H5` (Comune).
3. **`Neve accumulo!H10` branch condition reversed vs `Neve!H10`**: tool 1 uses `IF(as<200, qsk1, qsk2(as))`; tool 2 uses `IF(as<200, qsk2(as), qsk1)` — same table, opposite branch selection. Per NTC 2018 the constant qsk1 applies below 200 m and the altitude-formula qsk2 applies at/above 200 m, so tool 1's logic is the code-correct one and tool 2's is inverted.
4. **G29 roof-type selector is decorative**: `Neve!K30` only produces a text banner ("COPERTURA AD UNA FALDA!" / instruction to hide rows); nothing in the workbook actually suppresses computation of the non-selected roof type. Both D34 (1-pitch) and D60/H61 (2-pitch) are always computed — a re-implementation must pick the right output cell based on the user's stated roof type rather than trusting a "selected" flag from the sheet.
5. **Zona text "I (mediterranea))"** in `Tabelle!A4` has a stray extra closing parenthesis — cosmetic but an exact-string enum implementation must match it byte-for-byte or normalize it.
6. **μ shape-coefficient boundary gap**: `IF(AND(a>30,a<60), 0.8*(60-a)/30, 0)` is strict on both bounds, so a=30° or a=60° exactly fall to the `H30<30` false / final `0` branch respectively — at a=30° this evaluates to 0 rather than 0.8 (discontinuity), and the a<30 branch already returns 0.8 at a=30 is unreachable since a=30 fails `H30<30`. Net effect: a=30° yields μ=0.8·(60-30)/30=0 is wrong — recompute: AND(30>30,...)=FALSE since 30 is not >30, so it drops to else→0, while a=29.99° gives 0.8. Discontinuity at exactly 30°.
7. **Linear interpolation of `m1` (`M38`) can go negative** when `b2 > ls` far exceeds `m1`, since nothing clamps `M38` to a physical minimum (e.g. 0.8 per code). In the golden case `M38=-3.677` is computed but unused (falls into the `m1_final` false-branch); a b2<ls scenario would propagate this unclamped negative value straight to `H43`/design load.

## Golden test case

### Tool 1 (`Neve`, single pitch branch)
Input: comune=Mapello, as=250, topografia=Normale, Ct=1, tipo=Copertura ad una falda, a=0, parapetto=NO
Output: provincia=Bergamo, regione=Lombardia, zona="I (alpina)", qsk=1.55392 kN/m2, CE=1, μ=0.8, qs=1.24314 kN/m2

### Tool 1 (two-pitch branch, same H5/H9/H13/H26)
Input: a1=35°, parapetto1=NO, a2=50°, parapetto2=NO
Output: μ1=0.666667, qs1=1.03595 kN/m2, μ2=0.266667, qs2=0.414379 kN/m2

### Tool 2 (`Neve accumulo`)
Input: comune=Bergamo, as=249, topografia=Normale, Ct=1, b1=43.15, b2=36.2, h=10, γ=2, a=0, m1_input=0.8, msup=0.45
Output: zona="I (alpina)", qsk=1.5 kN/m2, CE=1, ls=15 m, γh/qsk=13.3333, μw_raw=3.9675, mw=3.9675, ms=0, m2=3.9675, K38(slope)=0.211167, L38=-4.47673, M38=-3.67673, m1_final=0.8, m2_final=3.9675, ls_final=15
