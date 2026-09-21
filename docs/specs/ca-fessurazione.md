# CA Fessurazione — spec

Unit covers NTC2018 §4.1.2.2.4/4.1.2.2.5 SLS checks for R.C. sections: stress
limitation and crack-width verification. 3 independently-usable tools + 1
shared lookup table (materiale-cls). Each check is applied to 3 sections
(h=30cm edge zone, h=30cm central zone, h=20cm) by simple row repetition —
collapsed below into one indexed calc per tool.

## Shared data: materiale-cls (concrete class properties)

Sheet `MATERIALE CLS`, table rows 3-14 (class `C8/10`…`C50/60`), key = col A
(class name string, exact match). Columns used downstream: E=fctm [MPa],
I=Ec [MPa] (labelled "Ec", NOT "Ecm" — see bug list). Formulas (row r, class Rck=B_r):
- `fck[r] = 0.83*B_r` (except row 9 `C30/37` and row 11 `C35/45` where fck is hardcoded, not `0.83*Rck` — see bugs)
- `fctm[r] = 0.3*fck[r]^(2/3)` (EC2 3.1.2 / NTC Tab 11.2.V)
- `Ec[r] = 22000*(fcm[r]/10)^0.3`, `fcm[r]=fck[r]+8`
- `Nmin[r] = MAX(0.26*fctm[r]/450*O16*O17, 0.0013*O16*O17)*10000` (As,min NTC §4.1.6; `450`=hardcoded fyk MPa; O16=bt=1 m, O17=d=0.2 m; `*10000` converts m²→cm²) — reference table, not wired into fessurazione outputs, listed for completeness only.
Other columns (F fctk, G fctd, H fcd, J/K Poisson, L/M shear modulus, P fcm(t)) not consumed by ca-fessurazione tools.
Full values: `build/data/ca-fessurazione/materiale-cls.csv`.

---

## Tool 1: verifica-limitazione-tensioni
Sheet `Limitazione delle tensioni`. Purpose: SLS stress-limitation check,
NTC2018 §4.1.2.2.5 — caps concrete compressive stress under rare (RAR) and
quasi-permanent (QPE) combos, and rebar tensile stress under RAR.

**Inputs**
| cell | symbol | meaning | unit | type | cached |
|---|---|---|---|---|---|
| C6 | Rck | characteristic cube strength | MPa | input | 45 |
| C8 | fyk | rebar yield (B450C) | MPa | input | 450 |
| D13,D21,D29 | σc,RAR[i] | acting concrete stress, rare combo, section i | MPa | input | 4.5 / 10 / 6 |
| D14,D22,D30 | σc,QPE[i] | acting concrete stress, quasi-perm combo, section i | MPa | input | 4.5 / 5.3 / 6 |
| D15,D23,D31 | σs,RAR[i] | acting rebar stress, rare combo, section i | MPa | input | 255.8 / 274 / 237 |

Sections i=1 "h=30cm" (edge), i=2 "h=30cm Zona centrale", i=3 "h=20cm".

**Outputs**
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| C7 | fck | `0.83*Rck` | MPa | 37.35 |
| C13/21/29 | σc,max,RAR | `0.6*fck` | MPa | 22.41 |
| C14/22/30 | σc,max,QPE | `0.45*fck` | MPa | 16.8075 |
| C15/23/31 | σs,max,RAR | `0.8*fyk` | MPa | 360 |
| E13..E31 | utilization | `acting/limit` | % | 0.20–0.76 |
| F13..F31 | pass/fail | `IF(limit>acting,"ok","non verificato")` | — | all "ok" |

**Calc steps**
1. `fck = 0.83*Rck` [C7]
2. `σc,max,RAR = 0.6*fck` [C13/21/29]
3. `σc,max,QPE = 0.45*fck` [C14/22/30]
4. `σs,max,RAR = 0.8*fyk` [C15/23/31]
5. `util = σ_acting/σ_max` [E13..E31]
6. `verdict = util<1 ? "ok" : "non verificato"` (compares limit>acting, equivalent) [F13..F31]

Constants: 0.6, 0.45 (NTC §4.1.2.2.5, combinazione rara/quasi-permanente concrete stress coeffs); 0.8 (rebar stress coeff under rara).
No lookup tables, no external links.

---

## Tool 2: verifica-apertura-fessure (detailed)
Sheet `Apertura delle fessure`. Purpose: NTC2018 §C4.1.2.2.4.5 crack-width
check (EC2-style, mean-spacing method with 1.7 factor).

**Inputs**
| cell | symbol | meaning | unit | type/enum | cached |
|---|---|---|---|---|---|
| E4 | class | concrete class | — | enum (`materiale-cls` col A) | "C28/35" |
| E5 | bar type | rebar bond type | — | enum {barre aderenza migliorata, barre lisce} | "barre aderenza migliorata" |
| E6 | load case | flessione / trazione semplice / trazione eccentrica | — | enum | "caso di flessione" |
| E7 | load duration | breve/lunga durata | — | enum | "lunga durata" |
| E8 | crack limit class | w1/w2/w3 | — | enum | "w3 (0.40 mm)" |
| E9 | s | bar spacing | mm | input | 200 |
| E10 | σs | stress in tension rebar at cracked section | MPa | input | 286 |
| E17 | Es | rebar modulus | MPa | input (const) | 210000 |
| E23 | h | section depth | mm | input | 250 |
| E26 | b | section width | mm | input | 1000 |
| E29,E30 | n1,ø1 | bar count/diam, group 1 | — /mm | input | 5 / 20 |
| E31,E32 | n2,ø2 | bar count/diam, group 2 | — /mm | input | 0 / 0 |
| E38 | c | rebar cover | mm | input | 35 |
| E41 | k3 | crack-spacing const | — | const | 3.4 |
| E42 | k4 | crack-spacing const | — | const | 0.425 |
| E25 | x | neutral-axis depth | mm | input | 75.84 |
| S5:T6, V5:W6, P5:Q6, Y5:Z7 | lookup tables | k1, k2, kt, w-limit tables | — | see below | — |

**Outputs**
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| E47 | ωk | characteristic crack width | mm | 0.275859 |
| E46 | wlim | crack-width limit (from E8 selection) | mm | 0.4 |
| D48 | verdict | pass/fail text with utilization % | — | "verifica è soddisfatta … 0.69" |

**Calc steps (dependency order)**
1. `d = h - ø1/2 - c` [E24] = 250-10-35=205
2. `ρreff = As/Ac,eff` [E36]: `As = (n1·ø1²+n2·ø2²)·π/4` [E35]; `Ac,eff = hc,ef·b` [E27]; `hc,ef = MIN(2.5·(h-d), (h-x)/3, h/2)` [E22]
3. `øeq = (n1·ø1²+n2·ø2²)/(n1·ø1+n2·ø2)` [E33] (NTC §C4.1.8)
4. `αe = Es/Ec` [E20], `Ec` from materiale-cls lookup (see below)
5. `k1 = VLOOKUP(bar_type, S5:T6)` [E39] — barre aderenza migliorata→0.8, barre lisce→1.6
6. `k2 = VLOOKUP(load_case, V5:W6)` [E40] (§C4.1.9) — flessione→0.5, trazione semplice→1, trazione eccentrica→`(ε1+ε2)/2/ε1` (row7, currently `#DIV/0!`, unused/dead — see bugs)
7. `kt = VLOOKUP(load_duration, P5:Q6)` [E43] — breve→0.6, lunga→0.4
8. `slim = 5·(c + øeq/2)` [E12]; branch: `slim > s` → use §C4.1.7 (Δsm from crack theory), else §C4.1.10 (Δsm = 0.75·crack spacing from RC theory) [H12/E15]
9. `Δsm(C4.1.7) = (k3·c + k1·k2·k4·øeq/ρreff)/1.7` [E13] (§C4.1.7)
10. `Δsm(C4.1.10) = 0.75·(E23−E25)` [E14] — NOTE: uses h and x, not a crack-spacing formula of the same family as step 9 (see bugs)
11. `Δsm,eff = IF(s<slim, Δsm(C4.1.7), Δsm(C4.1.10))` [E15]
12. `εsm = MAX((σs − kt·fctm/ρreff·(1+αe·ρreff))/Es, 0.6·σs/Es)` [E45] (§C4.1.6)
13. `wk = 1.7·εsm·Δsm,eff` [E47] (§C4.1.5)
14. `wlim = VLOOKUP(crack_limit_class, Y5:Z7)` [E46]: w1→0.2, w2→0.3, w3→0.4 mm
15. `verdict = IF(wk<wlim, "soddisfatta", "non soddisfatta") & utilization=ROUNDUP(wk/wlim,2)` [D48]

**External link**: `Ecm=VLOOKUP(class,'[1]MATERIALE CLS'!A3:P14,9,FALSE)` [E18] and `fctm=VLOOKUP(class,...,5,FALSE)` [E19] point to an **external workbook** (`[1]`), currently unavailable. Cached: Ecm=32588.1 MPa, fctm=2.83499 MPa for class C28/35 — these match the local `materiale-cls` sheet's Ec/fctm columns for the same class, so the external file is presumed a copy of that same table. **Any re-implementation should source Ec/fctm from the local materiale-cls table**, keyed by concrete-class string, since the external link cannot be resolved.

**Lookup tables**
| range | meaning | key | rule |
|---|---|---|---|
| S5:T6 | k1 by bar bond type | E5 string | exact match |
| V5:W6 (rows 5-6 only; row7 dead) | k2 by load case | E6 string | exact match |
| P5:Q6 | kt by load duration | E7 string | exact match |
| Y5:Z7 | wlim by crack class | E8 string | exact match |
| materiale-cls A3:P14 | Ec, fctm by class | E4 string | exact match |

---

## Tool 3: verifica-apertura-fessure-semplificata
Sheet `Apertura delle fessure SEMP`. Purpose: simplified crack-width check
(NTC §4.1.2.2.4) via direct rebar-stress limit tables (in lieu of full
ωk calc) — table-driven equivalent of Tool 2, cross-references Tool 1's
section labels.

**Inputs**
| cell | symbol | meaning | unit | type | cached |
|---|---|---|---|---|---|
| D21/D43/D66 | σs,lim(FRE) | stress limit, frequent combo, section i | MPa | input (per w3 class) | 280 |
| D22/D44/D67 | σs,lim(QPE) | stress limit, quasi-perm combo, section i | MPa | input (per w2 class) | 240 |
| E21/E43/E66 | σs,FRE | acting rebar stress, frequent combo | MPa | input | 231/206/180 |
| E22/E44/E67 | σs,QPE | acting rebar stress, quasi-perm combo | MPa | input | 218/233/171 |

**Outputs**
| cell | symbol | meaning | cached |
|---|---|---|---|
| F21..F67 | utilization | `E/D` | 0.64–0.97 |
| G21..G67 | verdict | `IF(D>E,"ok","non verificato")` | all "ok" |
| B19/41/64, B20/42/65 | section labels | linked from Tool 1 `B11/B12`, `B19/B20`, `B27/B28` | see bugs (B20,B65 render as `0`) |

**Calc steps**
1. `util = σs,acting / σs,limit` [F21..F67]
2. `verdict = limit>acting ? "ok" : "non verificato"` [G21..G67]
No formula derives the D-column limits (280/240 hardcoded inputs, presumably taken from EC2 Table 7.2N for w3/w2 crack classes at given bar diameter — not present in this sheet).

---

## Suspected bugs / fragile spots
- **Apertura-fessure E18/E19** (`[1]MATERIALE CLS'!...`): dead external link. Confirmed by re-reading formula text; cached values match local `materiale-cls` sheet for class C28/35, so treat local table as substitute.
- **Apertura-fessure W7** `=(W9+W10)/2/W9` → `#DIV/0!` (W9,W10 empty): dead/broken k2 branch for "caso di trazione eccentrica" in V5:W6-adjacent row7; not wired to any VLOOKUP range (k2 lookup range is `V5:W6`, excludes row 7), so this broken cell is currently inert but would break if the k2 table were ever extended to include row 7. Confirmed by reading V6/W6 range used in E40's VLOOKUP (only rows 5-6).
- **Apertura-fessure B39** label `=D7` ("durata carico") is wrong: cell computes `k1` via `VLOOKUP(E5,S5:T6,...)`, i.e. driven by `E5` "tipo barre", not `E7`/D7 "durata carico". Cosmetic (label only, doesn't affect k1's value) but re-implementers should not copy the mislabelled dependency. Confirmed by comparing B39 formula vs its VLOOKUP source cell.
- **materiale-cls fck column**: most rows compute `fck=0.83*Rck`, but row 9 (C30/37, fck cached 30.71) and row 11 (C35/45, `C11=35` hardcoded literal, fck=35 not `0.83*45=37.35`) break the pattern — inconsistent fill-down, `0.83*Rck` formula overwritten with a literal on at least row 11. Confirmed by reading row11: `C11=35` (constant) vs row10/12 which are formulas. Only affects entries not used by the golden case (class C28/35, row 8, which is a correct formula).
- **Apertura-fessure-semp B20/B65** = `'Limitazione delle tensioni'!B12` / `!B28`, both blank source cells → render as literal `0` instead of a subtitle string; B42 (same pattern, row 20) correctly resolves to "Zona centrale" because that source cell is populated. Inconsistent — re-implementation should treat missing subtitle as empty string, not `0`.
- **Δsm(C4.1.10)** [E14] `=0.75*(E23-E25)` uses `h` and `x` (neutral axis) directly, unlike the C4.1.7 branch which is a proper crack-spacing formula from k1..k4/ρ — worth double-checking against the source NTC circolare text for §C4.1.10 since the two branches use structurally different input sets (flag as "?", not fully re-derivable from the sheet alone).

## Golden test case
Tool 2 (verifica-apertura-fessure), full input→output:
```
class=C28/35, bar_type=barre aderenza migliorata, load_case=caso di flessione,
load_duration=lunga durata, crack_limit=w3 (0.40 mm), s=200mm, σs=286MPa,
Es=210000MPa, h=250mm, b=1000mm, n1=5, ø1=20mm, n2=0, ø2=0, c=35mm, x=75.84mm,
k3=3.4, k4=0.425
→ Ec=32588.1 MPa, fctm=2.83499 MPa, αe=6.44407, d=205mm, hc,ef=58.0533mm,
  Ac,eff=58053.3 mm², As=1570.8 mm², øeq=20mm, ρreff=0.0270578,
  slim=225mm (s=200<225 → use §C4.1.7), k1=0.8, k2=0.5, kt=0.4,
  Δsm=143.916mm, εsm=0.00112753, wk=0.275859mm, wlim=0.4mm,
  verdict="soddisfatta", utilization≈0.69
```
Tool 1 (verifica-limitazione-tensioni), section i=1 (h=30cm edge):
```
Rck=45MPa, fyk=450MPa, σc,RAR=4.5, σc,QPE=4.5, σs,RAR=255.8
→ fck=37.35, σc,max,RAR=22.41 (util 0.2008,"ok"), σc,max,QPE=16.8075 (util 0.2677,"ok"),
  σs,max,RAR=360 (util 0.7106,"ok")
```
