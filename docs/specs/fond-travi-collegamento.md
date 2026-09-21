# Fondazioni — Travi di Collegamento (Foundation Tie Beams) — Implementation Spec

Source workbook has 3 sheets: `Travi collegamento NTC2018`, `Travi colleg. EN 1998-1 e 5`, `Rif. Normativi T. Collegamento` (text-only reference sheet, no formulas — informational, not a tool). Plus shared `Tabelle` sheet (see below).
Governing code: NTC 2018 §7.2.5 / Circolare 2019 (tie-beam axial design force), EN 1998-1:2013 §5.8.2, EN 1998-5 §5.4.1.2 (geotechnical connection/tie requirement). Checks: axial compression, axial tension, slenderness, minimum stirrups; EN sheet adds min longitudinal reinforcement ratio and min section geometry.

## Tabelle sheet delta (vs strutture.shared.materials, from diff)

Concrete/steel/cover lookups (`M34:R41`, `M45:P49`, durability tables) are identical to `ca-travi` and already ported — reuse `strutture.shared.materials`. New tables specific to this unit, added at the bottom of `Tabelle` (rows 116-134), not present in `ca-travi`:

- `Tabelle!M117:P121` — **NTC 2018 soil category table** (used by NTC sheet): key = soil category (M: "A"/"B"/"C"/"D"), col N = `SS` raw factor (A: constant 1; B/C/D: formula referencing `'Travi collegamento NTC2018'!C5,C4` i.e. F0, ag — **cross-sheet hardcoded reference**, see bug below), col O = `SS` clamped via `IFS` to code-mandated bounds (A:1; B: clamp[1,1.2]; C: clamp[1,1.5]; D: clamp[0.9,1.8]), col P = coefficient α for the `±α·S·NEd` tie-force formula (A=0.2, B=0.3, C=0.4, D=0.6).
- `Tabelle!M124:N127` — **topographic category table**: key = category (M: T1-T4), N = `ST` (T1=1, T2=1.2, T3=1.2, T4=1.4).
- `Tabelle!M131:P134` — **EN 1998 soil category table** (used by EN sheet): key = soil (M: A-D), N = S for spectrum Type 1, O = S for Type 2, P = α coefficient (A=0, B=0.3, C=0.4, D=0.6). Selected N vs O column depends on `Ms` (surface-wave magnitude) ≤5.5 → Type1(N) else Type2(O).

Rows 96-113 (fire spacing/diameter tables) are unrelated fire_reduction tables reused from `ca-travi`, not used by this unit.

## Tool 1: `fond-travi-collegamento-ntc2018` — tie beam check, NTC 2018

### Purpose
Computes the seismic design axial tie force `NEd = amax·Nsd·α` per NTC 2018 §7.2.5 (?, table constants match Circolare 2019 tab. Comm. 7.11.I / EN 1998-1 §5.8.2 α values), then checks the beam section in pure axial compression and tension, checks slenderness λ against a code-derived limit λlim, and checks minimum stirrup area. Sheet `Travi collegamento NTC2018`.

### Inputs
| cell | symbol | meaning | unit | type/enum/range | cached example |
|---|---|---|---|---|---|
| C4 | ag | Max horizontal ground acceleration | g | number | 0.151 |
| C5 | F0 | Spectral amplification factor | - | number | 2.43 |
| C6 | soil | Soil category | - | enum A/B/C/D | "B" |
| C7 | topo | Topographic category | - | enum T1-T4 | "T1" |
| C11 | B | Beam section width | mm | number | 400 |
| C12 | H | Beam section height | mm | number | 400 |
| C13 | φ | Longitudinal bar diameter | mm | number | 16 |
| C14 | N. | Number of longitudinal bars | - | integer | 6 |
| C17 | class_c | Concrete class | - | enum (shared materials table) | "C25/30" |
| C18 | class_s | Steel class | - | enum (shared materials table) | "B450C" |
| C22 | N1 | Vertical force on footing 1 | kN | number | 2000 |
| C23 | N2 | Vertical force on footing 2 | kN | number | 2500 |
| C38 | l | Clear span of tie beam | mm | number | 5000 |
| C39 | β | Effective-length (buckling) coefficient | - | number | 1 |
| C48 | φ_st | Stirrup diameter | mm | number | 10 |
| C49 | N._st | Stirrup legs | - | integer | 2 |
| C50 | cf | Cover | mm | number | 40 |
| C53 | p | Stirrup spacing (design choice) | mm | number | 125 |

### Outputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| C8 | SS | Stratigraphic amplification coeff | - | 1.2 |
| C9 | ST | Topographic amplification coeff | - | 1 |
| C10 | S | S = SS·ST | - | 1.2 |
| C15 | Ac | Concrete section area | mm2 | 160000 |
| C16 | As | Longitudinal steel area | mm2 | 1206.37 |
| C19 | fck | Char. cylinder concrete strength | MPa | 24.9 |
| C20 | fcd | Design concrete compressive strength | MPa | 14.11 |
| C21 | fyd | Design steel yield strength | MPa | 391.304 |
| C24 | Nsd | Mean vertical force on connected elements | kN | 2250 |
| C27 | amax | Expected max horiz. accel. at site | g | 0.1812 |
| C28 | NEd | Design axial tie force | kN | 122.31 |
| C29 | Nc,Rd | Compression axial resistance | kN | 2257.6 |
| C30 | check_c | Nc,Rd > NEd — pass/fail | - | "OK" |
| C31 | T.L._c | Compression work ratio NEd/Nc,Rd | - | 0.054177 |
| C32 | Nt,Rd | Tension axial resistance | kN | 472.058 |
| C33 | check_t | Nt,Rd > NEd — pass/fail | - | "OK" |
| C34 | T.L._t | Tension work ratio NEd/Nt,Rd | - | 0.259099 |
| C40 | l0 | Effective buckling length | mm | 5000 |
| C41 | i | Radius of gyration | mm | 115.47 |
| C42 | λ | Slenderness | - | 43.3013 |
| C43 | λlim | Slenderness limit | - | 107.407 |
| C44 | check_λ | λlim > λ — pass/fail | - | "OK" |
| C45 | T.L._λ | Slenderness work ratio λ/λlim | - | 0.403151 |
| C51 | d | Effective depth | mm | 360 |
| C52 | pmax | Max stirrup spacing | mm | 288 |
| C54 | Ast,min | Min stirrup area (per m) | mm2/m | 600 |
| C55 | Ast | Provided stirrup area | mm2 | 157.08 |
| C56 | check_st | Ast(areal density)>Ast,min — pass/fail | - | "OK" |

### Calculation steps
1. `SS[C8] = VLOOKUP(soil[C6], Tabelle!M118:P121, col3="O")` — clamped stratigraphic coeff.
2. `ST[C9] = VLOOKUP(topo[C7], Tabelle!M124:N127, col2="N")`.
3. `S[C10] = SS[C8]·ST[C9]`.
4. `Ac[C15] = B[C11]·H[C12]`.
5. `As[C16] = π·φ[C13]²/4·N.[C14]`.
6. `fck[C19] = VLOOKUP(class_c[C17], Tabelle!M34:R41, col3)`.
7. `fcd[C20] = 0.85·fck[C19]/1.5`.
8. `fyd[C21] = VLOOKUP(class_s[C18], Tabelle!M45:P49, col2)/1.15`.
9. `Nsd[C24] = (N1[C22]+N2[C23])/2`.
10. `amax[C27] = ag[C4]·S[C10]`.
11. `NEd[C28] = amax[C27]·Nsd[C24]·α`, where `α = VLOOKUP(soil[C6], Tabelle!M118:P121, col4="P")` — the raw NTC coefficient (0.2/0.3/0.4/0.6 for A/B/C/D), i.e. `NEd = amax·Nsd·α` (kN, all inputs already kN/g-consistent). Per Rif.Normativi cell 42-44, sign convention is `±α·S·NEd_elements`; here `amax` already folds in `S`, so this reproduces `±α·amax·Nsd` (α absorbing the code's α·S product structure — see bug note).
12. `Nc,Rd[C29] = Ac[C15]·fcd[C20]/1000` (mm²·MPa/1000 → kN).
13. `check_c[C30] = Nc,Rd[C29] > NEd[C28] ? "OK" : "NO"`.
14. `T.L._c[C31] = NEd[C28]/Nc,Rd[C29]`.
15. `Nt,Rd[C32] = As[C16]·fyd[C21]/1000`.
16. `check_t[C33] = Nt,Rd[C32] > NEd[C28] ? "OK" : "NO"`.
17. `T.L._t[C34] = NEd[C28]/Nt,Rd[C32]`.
18. `l0[C40] = l[C38]·β[C39]`.
19. `i[C41] = sqrt( (min(B,H)³·max(B,H)/12) / (B·H) )` — radius of gyration about weak axis of rectangle.
20. `λ[C42] = l0[C40]/i[C41]`.
21. `λlim[C43] = 25/sqrt( NEd[C28]·1000/(Ac[C15]·fcd[C20]) )`.
22. `check_λ[C44] = λlim[C43] > λ[C42] ? "OK" : "NO"`.
23. `T.L._λ[C45] = λ[C42]/λlim[C43]`.
24. `d[C51] = H[C12] - cf[C50]`.
25. `pmax[C52] = min(0.8·d[C51], 1000/3)`.
26. `Ast,min[C54] = 1.5·B[C11]` (mm²/m, NTC minimum transverse reinforcement rule).
27. `Ast[C55] = π·φ_st[C48]²/4·N._st[C49]` (area of one stirrup set, mm²).
28. `check_st[C56] = (Ast[C55]·1000/p[C53]) > Ast,min[C54] ? "OK" : "NO"` — converts provided stirrup area to an areal density (mm²/m) using spacing `p`, then compares against Ast,min.

### Lookup tables
- `Tabelle!M118:P121` key=soil letter (A-D): N=raw SS (hardcoded formula referencing this same sheet's C4/C5, exact match), O=clamped SS (`IFS` bounds), P=α coefficient. Exact-match VLOOKUP on soil letter.
- `Tabelle!M124:N127` key=topo category T1-T4, N=ST, exact match.
- `Tabelle!M34:R41`, `M45:P49`: concrete/steel class tables — shared with `strutture.shared.materials` (see `ca-travi` spec).

### Constants
- `fcd` factor `0.85/1.5` (NTC §4.1.2.1.1.1, γc=1.5, αcc=0.85).
- `fyd` divisor `1.15` (γs=1.15).
- `Ast,min = 1.5·B` mm²/m — minimum transverse reinforcement areal density rule for tie beams.
- `λlim` formula constant `25` — empirical/code slenderness coefficient (NTC-side buckling check, distinct from EN sheet's Eurocode-style formula).
- `pmax = min(0.8d, 1000/3)` — 1000/3 ≈ 333 mm hardcoded max spacing cap.
- unit conversion `/1000` in Nc,Rd/Nt,Rd/λlim (N → kN, since mm²·MPa = N).

## Tool 2: `fond-travi-collegamento-en1998` — tie beam check, EN 1998-1/EN 1998-5 (delta vs Tool 1)

Sheet `Travi colleg. EN 1998-1 e 5`. Same section/material inputs (C9-C22 mirror C11-C24 of the NTC sheet, offset by 2 rows and default H=450mm/N.=8 bars instead of 400mm/6). Differences:

- **No F0/topographic input.** Instead `Ms[C6]` (surface-wave magnitude) selects spectrum type: `TIPO[C7] = Ms≤5.5 ? "TIPO1" : "TIPO2"` (cached example: Ms=5.6 → "TIPO2").
- `S[C8] = VLOOKUP(soil[C5], Tabelle!M131:O134, col = TIPO1?3:2)` i.e. col N (Type1) or col O (Type2), exact match on soil A-D. No SS/ST split, no clamping — raw table value used directly.
- `amax[C25] = ag[C4]·S[C8]` (step 10 analog).
- `NEd[C26] = amax[C25]·Nsd[C22]·α`, `α = VLOOKUP(soil[C5], Tabelle!M131:P134, col4="P")` — EN α values (A=0, B=0.3, C=0.4, D=0.6; note A=0 vs NTC's A=0.2, see bug note).
- `Nc,Rd[C27]`, `Nt,Rd[C30]` identical formulas to NTC steps 12/15, using Ac[C13]/fcd[C18], As[C14]/fyd[C19].
- **Slenderness uses Eurocode buckling-curve style formula**, not the NTC `25/sqrt(...)` rule:
  - `ω[C40] = As·fyd/(Ac·fcd)` — mechanical reinforcement ratio (dimensionless, cached 0.247819).
  - `λlim[C42] = 20·0.7·sqrt(1+2ω)·0.7/sqrt(NEd·1000/(Ac·fcd))` — this is EN 1992-1-1 §5.8.3.1 slenderness-limit formula with factors A=0.7 (assumed, since φef not given), B=`sqrt(1+2ω)`, C=0.7 (assumed rm=1 → C=1.7-rm=0.7), all pre-baked as literal `0.7` constants rather than computed from φef/rm inputs (i.e. simplified/fixed-coefficient variant of the general EC2 formula: `λlim = 20·A·B·C/√n`).
  - `check_λ[C43] = λlim[C42] > λ[C41] ? "OK" : "NO"`; `T.L.[C44] = λ[C41]/λ[C42]` (note: numerator is `λ` not `NEd`-based, same pattern as NTC sheet).
- **Extra checks not in NTC sheet** (EN 1998-1 §5.8.2 / Rif.Normativi items 2-4):
  - `ρb[C47] = 0.008·Ac[C13]` (min longitudinal reinf area, 0.8%); `check[C48] = ρb < As[C14]`.
  - `N.floors[C49]` input (user); `bw,min[C50]=250mm` constant; `check[C51] = bw,min < B[C9]`.
  - `hw,min[C52] = N.floors≤3 ? 400 : 500` mm; `check[C53] = hw,min ≤ H[C10]`.
- **Stirrup check differs**: adds inclination `α_st[C58]` (default 90°), uses `pmax[C61] = min(0.75·d·(1+1/tan(rad(α_st))), 600)` mm (EC2-style, vs NTC's `0.8d` rule), and instead of an absolute Ast,min it computes a **minimum stirrup percentage** `ρmin[C63] = 0.08·sqrt(fck)/fyd` (fck/fyd looked up directly via VLOOKUP, not reusing C17/C18 cells) compared against provided `ρ[C64] = π·φ_st²/4·N._st/(B·p)`; `check[C65] = ρ > ρmin`.

### Lookup tables
- `Tabelle!M131:P134` key=soil A-D: N=S(Type1), O=S(Type2), P=α coefficient. Exact match, column choice (N vs O) driven by `Ms` magnitude branch.

### Constants
- Spectrum-type magnitude threshold `Ms=5.5` (EN 1998-1 §3.2.2.2, Type 1 vs Type 2 spectra split, cached Ms=5.6 → Type 2).
- `ρb,min = 0.008` (0.8%) — EN 1998-1 §5.8.2(4)? min longitudinal ratio.
- `bw,min=250mm`; `hw,min` 400/500mm split at 3 floors — Rif.Normativi items 2-3.
- `ρmin = 0.08·sqrt(fck)/fyd` — EC2 §9.2.2 minimum shear-reinforcement ratio formula reused for stirrups.
- `pmax` cap `600mm` (EC2 max stirrup spacing absolute cap) vs NTC's `1000/3≈333mm` cap — different code, different limit.

## Suspected spreadsheet bugs / fragile spots

1. **Cross-sheet hardcoded reference in shared `Tabelle!N119:N121`.** The NTC soil-B/C/D raw-SS formulas literally reference `'Travi collegamento NTC2018'!C5` and `!C4` (F0, ag) instead of taking them as lookup/table parameters. If this table were reused by another sheet/tool with different ag/F0, the SS value would silently use the NTC sheet's current input values, not the calling sheet's. Confirmed by re-reading raw formulas in the diff (`N119={=1.4-0.4*'Travi collegamento NTC2018'!C5*'Travi collegamento NTC2018'!C4}` etc.) — this is a spreadsheet anti-pattern, not a bug in output for the single-workbook case, but a landmine for any re-implementation that tries to make the SS table generic.
2. **α at soil A differs sign/meaning between codes but both applied identically to NEd.** NTC table gives α_A=0.2 (Tabelle!P118) while EN table gives α_A=0 (Tabelle!P131) — for soil A, EN 1998-5 §5.4.1.2 point 5 states tie beams "are not necessary... for type A ground", consistent with α=0 zeroing NEd; NTC's α_A=0.2 does not zero it, meaning the NTC tool would still report a non-trivial required tie force even on soil A. This divergence looks intentional (different codes) but should be flagged since it means the two tools give materially different NEd for identical geometry/soil-A inputs.
3. **Column-index brittleness**: NTC `VLOOKUP(...,4,FALSE)` for α at C28 hardcodes column 4 of `M118:P121`; if the shared Tabelle range is ever resequenced (e.g. inserting a column), this silently returns the wrong constant with no validation. Same risk on EN sheet's `VLOOKUP(...,IF(Ms<=5.5,3,2),...)` — computed column index into a 4-col table, fragile against reordering.
4. **`check_λ` comparisons are inverted-looking but consistent**: both sheets compute `IF(λlim>λ,"OK","NO")`, i.e. label text is "λ > λlim" (C44/H NTC row44 label) yet the actual comparison tests `λlim > λ`; label and comparison direction are swapped in the row label string, purely cosmetic (values are correct) but worth flagging so the Python port doesn't invert the true condition by matching the label instead of the formula.
5. **EN sheet's `ρmin[C63]` re-derives fck/fyd via fresh `VLOOKUP` on `class_c[C15]`/`class_s[C16]`** instead of reusing already-computed `C17`(fck)/`C19`(fyd) cells — redundant but not a correctness bug (same source table), just duplicated lookup logic to preserve in the port only if bit-exact cell tracing is required; otherwise reuse the already-computed values.

## Golden test case

### Tool 1 (NTC 2018, `Travi collegamento NTC2018`)
```
ag=0.151 g, F0=2.43, soil=B, topo=T1, B=400mm, H=400mm, φ=16mm, N.=6,
class_c=C25/30, class_s=B450C, N1=2000kN, N2=2500kN, l=5000mm, β=1,
φ_st=10mm, N._st=2, cf=40mm, p=125mm
→
SS=1.2, ST=1, S=1.2, Ac=160000mm2, As=1206.37mm2, fck=24.9MPa, fcd=14.11MPa,
fyd=391.304MPa, Nsd=2250kN, amax=0.1812g, NEd=122.31kN,
Nc,Rd=2257.6kN, check_c="OK", T.L._c=0.054177,
Nt,Rd=472.058kN, check_t="OK", T.L._t=0.259099,
l0=5000mm, i=115.47mm, λ=43.3013, λlim=107.407, check_λ="OK", T.L._λ=0.403151,
d=360mm, pmax=288mm, Ast,min=600mm2/m, Ast=157.08mm2, check_st="OK"
```

### Tool 2 (EN 1998, `Travi colleg. EN 1998-1 e 5`)
```
ag=0.151 g, soil=B, Ms=5.6 (→TIPO2), B=400mm, H=450mm, φ=16mm, N.=8,
class_c=C25/30, class_s=B450C, N1=2000kN, N2=2500kN, l=5000mm, β=1,
N.floors=3, φ_st=10mm, N._st=2, α_st=90°, cf=40mm, p=200mm
→
S=1.2, Ac=180000mm2, As=1608.5mm2, fcd=14.11MPa, fyd=391.304MPa, Nsd=2250kN,
amax=0.1812g, NEd=122.31kN,
Nc,Rd=2539.8kN, check_c="OK", T.L._c=0.0481573,
Nt,Rd=629.411kN, check_t="OK", T.L._t=0.194324,
i=115.47mm, ω=0.247819, λ=43.3013, λlim=54.6145, check_λ="OK", T.L._λ=0.792853,
ρb=1440mm2, check_ρb="OK", bw,min=250mm, check_bw="OK", hw,min=400mm, check_hw="OK",
d=410mm, pmax=307.5mm, ρmin=0.000887109, ρ=0.0019635, check_st="OK"
```
