# Pavimento Industriale (Industrial Ground Slab) — Implementation Spec

Source workbook `pavimento-industriale.xlsx`, sheets: `carichi_distribuiti_concentrati` (main), `Winkler`, `Materiali`, `Eisenman`.
Governing doc: CNR-DT 211/2014 (industrial floor slabs on grade, Westergaard/Losberg-type formulas), punching-shear checks per EC2 §6.4 / NTC2018 §4.1.2.1.3, crack/stress checks per EC2 §7. Column layout on the main sheet: B:D materials/geometry (shared), F:I distributed loads, K:O concentrated load "ruota motrice" (single wheel), Q:U concentrated load "ruote anteriori" (front wheel pair), continuing down into F "giunti" (joint) prescriptions and K/Q crack+reinforcement checks for the concentrated cases.

## Shared base: `pav-fondazione-materiali` — materials, geometry, Winkler subgrade, plate stiffness

### Purpose
Derives concrete/steel design properties (NTC2018 §11.2.10.?, EC2 §3.1), Winkler subgrade modulus, slab flexural rigidity and Westergaard radius of relative stiffness `l`, feeding both load tools below. No governing-clause number stamped on cells; formulas match EC2/CNR-DT211 conventions.

### Inputs
| cell | symbol | meaning | unit | type/enum | cached |
|---|---|---|---|---|---|
| C4 | CLS | concrete class | - | dropdown, `Materiali!$A$2:$A$10` (C20/25…C50/60) | "C25/30" |
| C7 | γc | concrete partial factor | - | number | 1.5 |
| C15 | ν | Poisson ratio | - | number | 0.2 |
| C18 | acciaio | steel grade | - | dropdown-like, `Materiali!E2` only has "B450C" | "B450C" |
| C20 | γs | steel partial factor | - | number | 1.15 |
| C24 | sottofondo | subgrade type | - | enum `Winkler!A2:A5`: soffice/mediocre/materiale di riporto costipato/molto costipato | "materiale di riporto costipato" |
| C27 | h | slab thickness | mm | number | 200 |
| C28 | c | cover | mm | number | 30 |
| `Materiali!A2:C10` | Tabella1 | table: 1 row = concrete class; cols A class(key), B Rck, C fck | MPa | fixed reference data | 9 rows |
| `Materiali!E2:F2` | Tabella2 | table: steel class(key,E) → fyk(F) | MPa | fixed reference data | 1 row |
| `Winkler!A2:C5` | Winkler table | 1 row = subgrade type; cols A type(key), B k [not used], C k' (=k/100, N/mm3) | N/mm3 | fixed reference data | 4 rows |

### Outputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| C5/C6 | Rck/fck | concrete strengths | MPa | 30 / 25 |
| C8 | fcd | design compressive strength | MPa | 14.1667 |
| C9/C10 | fcm/fctm | mean comp. / mean tensile strength | MPa | 33 / 2.60682 |
| C11/C12/C13 | fcfm/fcfk/fcfd | mean/characteristic/design flexural tensile strength | MPa | 3.12819 / 2.18973 / 1.45982 |
| C14 | Ecm | concrete elastic modulus | MPa | 31475.8 |
| C19/C21 | fyk/fyd | steel yield strengths | MPa | 450 / 391.304 |
| C26 | kT | subgrade modulus (Winkler k') | N/mm3 | 0.06 |
| C29 | d | effective depth = h−c | mm | 170 |
| C30 | λ | plate stiffness parameter | mm⁻¹ | 0.000919499 |
| C31 | W | section modulus, 1 m strip | mm³/m | 6.66667e6 |
| C32 | l | Westergaard radius of relative stiffness | mm | 776.901 |
| C33 | k | EC2 shear size factor | - | 2 |
| C34 | vmin | EC2 min shear stress | MPa | 0.494975 |
| C35 | v | EC2 shear strength reduction factor v1 | - | 0.54 |

### Calculation steps
1. `Rck[C5]=VLOOKUP(CLS[C4],Tabella1,2)`; `fck[C6]=VLOOKUP(CLS[C4],Tabella1,3)`.
2. `fcd[C8]=0.85·fck[C6]/γc[C7]`.
3. `fcm[C9]=fck[C6]+8`.
4. `fctm[C10]=0.27·Rck[C5]^(2/3)` (note: uses **Rck**, not fck, unlike standard EC2 0.30·fck^(2/3) — CNR-DT211-specific fit).
5. `fcfm[C11]=1.2·fctm[C10]`.
6. `fcfk[C12]=0.7·fcfm[C11]`.
7. `fcfd[C13]=fcfk[C12]/γc[C7]`.
8. `Ecm[C14]=22000·(fcm[C9]/10)^0.3`.
9. `fyk[C19]=VLOOKUP(acciaio[C18],Tabella2,2)`; `fyd[C21]=fyk[C19]/γs[C20]`.
10. `kT[C26]=VLOOKUP(sottofondo[C24],Winkler!A2:C5,3,FALSE)` (col C = k/100).
11. `d[C29]=h[C27]−c[C28]`.
12. `λ[C30]=(3·kT[C26]/(Ecm[C14]·h[C27]^3))^0.25`.
13. `W[C31]=1000·h[C27]^2/6`.
14. `l[C32]=((Ecm[C14]·h[C27]^3)/(12·(1−ν[C15]^2)·kT[C26]))^0.25` — classical Westergaard `l=(D/k)^0.25`.
15. `k[C33]=MIN(1+SQRT(200/d[C29]),2)` (EC2 6.4.4).
16. `vmin[C34]=0.035·k[C33]^1.5·fck[C6]^0.5` (EC2 6.2.2).
17. `v[C35]=0.6·(1−fck[C6]/250)` (EC2 6.2.2, v1).

### Lookup tables
- `Materiali!A2:C10`: key=class text (A), Rck (B), fck (C); exact match.
- `Materiali!E2:F2`: key="B450C" (E), fyk (F); single-row exact match.
- `Winkler!A2:C5`: key=subgrade description (A); returns col C (k'=k/100 N/mm3), exact match.

### Constants
- 0.85 (fcd), 8 MPa (fcm offset), 0.27/0.7 (fctm/fcfk fit coefficients — CNR-DT211 not standard EC2 0.30/0.7·fctm), 22000/0.3 (Ecm, EC2 3.1.3), 0.035/1.5/0.5 (vmin, EC2 6.2.2), 0.6/250 (v1, EC2 6.2.2).

## Tool: `pav-carichi-distribuiti` — uniformly distributed load check

### Purpose
Slab bending/cracking/reinforcement check under a UDL, using Westergaard's infinite-plate-on-Winkler-foundation moment coefficients. CNR-DT211/2014 §? (uncertain clause).

### Inputs
| cell | symbol | meaning | unit | type | cached |
|---|---|---|---|---|---|
| G4 | G | permanent distributed load | daN/m² | number | 0 |
| G5 | γG | partial factor, permanent | - | number | 1.3 |
| G6 | Q | variable distributed load | daN/m² | number | 2600 |
| G7 | γQ | partial factor, variable | - | number | 1.5 |
| G8 | ψ1 | frequent-combination factor | - | number | 0.9 |
| G31/H31 | ø | mesh rebar diameter (top/bottom, same value) | mm | number | 8 |
| G32/H32 | S | mesh spacing | mm | number | 200 |

### Outputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| G9/G10 | G,Q [kN/m²] | loads converted | kN/m² | 0 / 26 |
| G11 | qSLU | ULS combined load | kN/m² | 39 |
| G12 | qSLE,freq | frequent SLS combined load | kN/m² | 23.4 |
| G16/H16 | M_SLU sup/inf | ULS bending moment | Nmm/m | 7758.68 / 7435.78 |
| G17/H17 | M_SLE,f sup/inf | frequent SLS bending moment | Nmm/m | 4655.21 / 4461.47 |
| G21/H21 | σc,max sup/inf | ULS concrete flexural stress | MPa | 1.1638 / 1.11537 |
| G22/H22 | TL (stress) sup/inf | utilization = σ/strength | - | 0.531482 / 0.764045 — **PASS if ≤1** |
| G26/H26 | σc,t sup/inf | frequent-SLS tensile stress | MPa | 0.698281 / 0.669221 |
| G27/H27 | TL (crack) sup/inf | utilization vs fctm/1.2 | - | 0.32144 / 0.308063 — **PASS if ≤1** |
| G33/H33 | As | mesh area | mm²/m | 251.327 |
| G34/H34 | Mrd | reinforced-section moment capacity | Nmm/m | 15046.9 |
| G35/H35 | TL (rebar) | utilization = M_SLU/Mrd | - | 0.515634 / 0.494175 — **PASS if ≤1** |

### Calculation steps
1. `G_kNmq[G9]=G4/100`; `Q_kNmq[G10]=G6/100` (daN/m²→kN/m², ÷100).
2. `qSLU[G11]=G9·γG[G5]+G10·γQ[G7]`.
3. `qSLE,f[G12]=G9+G10·ψ1[G8]`.
4. `M_SLU,sup[G16]=(0.1682·qSLU[G11]/λ[C30]^2)/1000`; `M_SLU,inf[H16]=(0.1612·qSLU/λ^2)/1000` — Westergaard infinite-slab UDL moment coefficients (top=0.1682, bottom=0.1612), `/1000` unit-fix baked in.
5. `M_SLE,f[G17,H17]` same formulas with `qSLE,f[G12]`.
6. `σc,max[G21]=M_SLU,sup[G16]/W[C31]·1000`; `[H21]=M_SLU,inf[H16]/W[C31]·1000`.
7. `TL[G22]=σc,max,sup[G21]/fcfk[C12]`; `TL[H22]=σc,max,inf[H21]/fcfd[C13]` — **note denominators differ (fcfk vs fcfd), see §7 bug 1**.
8. `σc,t[G26]=M_SLE,f,sup[G17]/W[C31]·1000`; `[H26]` analogous with `H17`.
9. `TL(crack)[G27,H27]=σc,t/(fctm[C10]/1.2)` (hardcoded `/1.2` de-rating factor, unverified clause).
10. `As[G33]=ø[G31]^2·π/4·1000/S[G32]` (mm²/m of mesh, sup=inf same input).
11. `Mrd[G34]=As[G33]·0.9·d[C29]·fyd[C21]/1000` (simplified lever-arm 0.9d capacity).
12. `TL(rebar)[G35]=M_SLU,sup[G16]/Mrd[G34]`; `[H35]=M_SLU,inf[H16]/Mrd[H34]`.

### Constants
0.1682/0.1612 (Westergaard UDL center moment coefficients, sup/inf), `/1000` unit conversions, `/1.2` crack strength de-rating, `0.9` lever-arm factor.

## Tool: `pav-carichi-concentrati` — wheel/point load check (2 cases × 3 positions)

### Purpose
Westergaard point-load stresses at slab centro/bordo/spigolo (interior/edge/corner) for two independent wheel-load cases ("ruota motrice" cols K:O, "ruote anteriori" cols Q:U), plus punching-shear (EC2 §6.4), crack and reinforcement checks. CNR-DT211/2014 §? (uncertain clause; β/u1 pattern matches EC2 6.4.3).

### Inputs (per case, both K:O "ruota motrice" and Q:U "ruote anteriori" — 3 columns L/M/N or R/S/T = centro/bordo/spigolo)
| cell(s) | symbol | meaning | unit | type | cached (K-block) |
|---|---|---|---|---|---|
| L4:N4 (R4:T4) | P | wheel load, same value all 3 positions | kN | number | 15.5 (8) |
| L5:N5 | γ | partial factor | - | number | 1.5 |
| L6:N6 | ψ1 | frequent factor | - | number | 0.9 |
| L9:N9 (R9:T9) | bx | contact patch, x-dim | mm | number | 500 (100) |
| L10:N10 | by | contact patch, y-dim | mm | number | 100 (100) |
| L27:N27 | β | punching enhancement factor: centro 1.15/bordo 1.4/spigolo 1.5 | - | fixed per position (EC2 6.4.3-style) | 1.15/1.4/1.5 |
| L44:N44 (position header) | ø | crack-check mesh diameter | mm | number | 8 |
| L45:N45 | S | mesh spacing | mm | number | 200 |

### Outputs (per position, K-block cached shown; Q-block analogous with smaller P)
| cell | symbol | meaning | unit | cached (centro/bordo/spigolo) |
|---|---|---|---|---|
| L7:N7 | P_SLU | ULS load | kN | 23.25/23.25/23.25 |
| L8:N8 | P_SLE,f | frequent SLS load | kN | 13.95/13.95/13.95 |
| L11:N11 | Ac | contact area | mm² | 50000 (all) |
| L12:N12 | rr | equivalent contact radius | mm | 126.157 (all) |
| L13:N13 | b | Westergaard corrected contact radius | mm | 120.861 (all, same bx/by ⇒ same) |
| L21:N21 | σc,max | ULS stress at position (Westergaard) | MPa | 0.789861/1.19436/1.02311 |
| L22:N22 | TL(stress) | =σc,max/fcfd | - | 0.541068/0.818153/0.70085 — PASS ≤1 |
| L27:N27→L28:N28 | VEd | punching design shear = P_SLU·β | kN | 26.7375/32.55/34.875 |
| L28→L29 (as printed) u0 | perimeter, basic control | mm | 1200 (all) |
| L30:N30 | VRd,max | max punching stress = 0.5·v·fcd | MPa | 3.825 (all) |
| L31:N31 | vEd0 | punching stress at u0 | MPa | 0.131066/0.159559/0.170956 |
| L32:N32 | TL(punch,u0) | vEd0/VRd,max | - | PASS ≤1 |
| L33:N33 | u1 | control perimeter at 2d (see §7 bug 2) | mm | 3336.28/1956.64/1228.32 |
| L34:N34 | VRd,c | =vmin (global) | MPa | 0.494975 |
| L35:N35 | vEd1 | punching stress at u1 | MPa | 0.0471421/0.097857/0.167015 |
| L36:N36 | TL(punch,u1) | vEd1/VRd,c | - | PASS ≤1 |
| L40:N40 | σc,t | frequent-SLS tensile stress (Westergaard, using P_SLE,f) | MPa | 0.473917/0.716614/0.613868 |
| L41:N41 | TL(crack) | σc,t/(fctm/1.2) | - | 0.218158/0.329879/0.282583 — PASS ≤1 |
| L47:N47 | As | mesh area | mm²/m | 251.327 (all) |
| L48:N48 | Mrd | reinforced moment capacity | Nmm/m | 15046.9 (all) |
| L17:N17 | M_SLU | back-derived nominal moment = σc,max·h²/6 | Nmm/m | 5265.74/7962.38/6820.76 |
| L49:N49 | TL(rebar) | M_SLU/Mrd | - | 0.349956/0.529172/0.453301 — PASS ≤1 |

### Calculation steps
1. `Ac=bx·by`; `rr=SQRT(Ac/π)`.
2. `b = IF(rr/h<1.724, SQRT(1.6·rr^2+h^2)−0.675·h, rr)` (Westergaard equivalent-radius correction).
3. `P_SLU=P·γ`; `P_SLE,f=P·ψ1` (all 3 position columns reference the same `γ`/`ψ1` cell via absolute ref, e.g. `$L$6`, even under M/N — harmless since values are equal).
4. Position-specific Westergaard stresses (using `P_SLU` for σc,max, `P_SLE,f` for σc,t, same formula shape):
   - centro: `σ = 1.264·(P·1000)/h^2·(LOG10(l/b)+0.267)`.
   - bordo: `σ = 2.288·(P·1000)/h^2·(LOG10(l/b)+0.09)`.
   - spigolo: `σ = 3·(P·1000)/h^2·(1−1.23·(rr/l)^0.6)`.
5. `TL(stress)=σc,max/fcfd[C13]`.
6. `M_SLU[row17] = σc,max·h[C27]^2/6` (nominal per-mm moment, no /1000 — different scaling than the distributed tool's W).
7. `VEd=P_SLU·β`; `u0=2·(bx+by)` (same for all 3 positions).
8. `VRd,max=0.5·v[C35]·fcd[C8]`; `vEd0=(VEd·1000)/(u0·d)`; `TL=vEd0/VRd,max`.
9. `u1`: centro `=u0+4·d·π`; bordo `=2·MIN(bx,by)+MAX(bx,by)+2·h·π`; spigolo `=bx+by+h·π` — **bordo/spigolo use h, not d (see §7 bug 2)**.
10. `VRd,c=vmin[C34]` (global constant, position-independent); `vEd1=(VEd·1000)/(u1·d)`; `TL=vEd1/VRd,c`.
11. `σc,t`: same 3 position formulas as step 4 but with `P_SLE,f` in place of `P_SLU`; `TL(crack)=σc,t/(fctm[C10]/1.2)`.
12. `As=ø^2·π/4·1000/S`; `Mrd=As·0.9·d·fyd/1000`.
13. `TL(rebar)=M_SLU[row17]/Mrd`.
14. Repeat all steps identically for the Q:U "ruote anteriori" block (own P, bx, by; shares global C-column base values).

### Constants
1.264/0.267 (centro), 2.288/0.09 (bordo), 3/1.23/0.6 (spigolo) — Westergaard/PCA point-load coefficients (LOG = log10); 1.724/1.6/0.675 (Westergaard radius correction); 0.5 (VRd,max), `/1.2` crack de-rating, `0.9` lever-arm.

## Tool: `pav-giunti` — joint spacing/thickness prescriptions

### Purpose
Geometric rules-of-thumb for contraction, isolation, construction, expansion joint layout (no code clause stamped; CNR-DT211/2014 §? indicative practice).

### Inputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| C39/C40 | a'/b' | contraction-panel plan dims | m | 20 / 18 |
| C41/C42 | a/b | isolation-joint panel dims | m | 30.9 / 21.2 |
| C43 | α | thermal expansion coeff | 1/°C | 1e-5 |
| C44 | ΔT° | design temperature range | °C | 30 |

### Outputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| G39 | a'/b' ratio | contraction panel aspect | - | 1.11111 |
| I39 | check | "OK" if ratio<1.5, else "ATTENZIONE" (label says <1.2, see §7 bug 3) | - | "OK" |
| G40/H40 | Lmax | max contraction-panel size | cm | 460 |
| G41/H41 | joint filler thickness (isolation) | mm | 40 |
| G47 | a/b ratio | isolation panel aspect | - | 1.45755 |
| I47 | check | "OK" if ratio<1.5 else "ATTENZIONE" | - | "OK" |
| G50/H50 | sp | expansion-joint gap | mm | 9.27 |

### Calculation steps
1. `ratio1[G39]=a'[C39]/b'[C40]`; `check1[I39]=IF(G39<1.5,"OK","ATTENZIONE")`.
2. `Lmax[G40]=18·(h[C27]/10)+100` cm (h in mm → cm via /10).
3. `t_iso[G41]=h[C27]/5` mm.
4. `ratio2[G47]=a[C41]/b[C42]`; `check2[I47]=IF(G47<1.5,"OK","ATTENZIONE")`.
5. `sp[G50]=α[C43]·ΔT[C44]·MAX(a[C41],b[C42])·1000` mm (m→mm via ×1000).

### Constants
18, 100 (Lmax cm formula), 5 (isolation thickness divisor h/5), threshold 1.5 (both aspect checks; label text on row39 says "<1.2" — mismatched, see §7 bug 3).

## Tool: `pav-eisenman` — multi-wheel superposition coefficient (lookup only)

### Purpose
Standalone lookup table, no formulas in the workbook reference it — presumed manual aid for the Eisenmann method of superposing stresses from multiple adjacent wheel loads (not covered by the single-wheel Westergaard formulas above). Governing clause **uncertain (?)**; not wired into `carichi_distribuiti_concentrati`.

### Inputs
| range | symbol | meaning | unit | type |
|---|---|---|---|---|
| `Eisenman!A1:A160` | x | presumed distance-to-radius-of-relative-stiffness ratio (a/l) | - | 0.20 → 3.38, step ≈0.02 |

### Outputs
| range | symbol | meaning |
|---|---|---|
| `Eisenman!B1:B160` | coeff | dimensionless superposition/influence coefficient, monotonically decreasing 0.1921→0.0008 |

### Calculation steps
1. `coeff = interp(x, Eisenman!A:B)` — linear interpolation between the two bracketing rows (table is a fine-step, near-monotonic curve; no formula evidence of the interpolation rule, assumed linear).

### Lookup tables
`Eisenman!A1:B160`: key=x (A, ascending, step≈0.02, non-uniform near tail), value=coeff (B). Full data in `build/data/pavimento-industriale/eisenman.csv`.

## Suspected spreadsheet bugs / fragile spots (all re-verified against formulas above)

1. **Inconsistent stress-check denominators, distributed tool**: `G22 = G21/$C$12` (fcfk, characteristic) but `H22 = H21/$C$13` (fcfd, design) — same check pair (sup/inf) uses two different strength bases; sup should very likely also divide by fcfd for consistency with every other TL check in the sheet.
2. **Punching control-perimeter `u1` uses `h` instead of `d` for edge/corner**: interior (`L33=u0+4·$C$29(d)·π`) correctly uses effective depth `d`, but edge (`M33=...+2·$C$27(h)·π`) and corner (`N33=...+$C$27(h)·π`) use total thickness `h`. EC2 6.4.2 defines the 2d-offset control perimeter using `d` for all three cases; edge/corner perimeters are therefore ~18% oversized here (using h=200 vs d=170), understating `vEd1` and non-conservatively passing the punching check.
3. **Joint-check label/threshold mismatch**: row 39 label says `"a/b<1.2"` but the actual formula `I39=IF(G39<1.5,"OK","ATTENZIONE")` tests against 1.5, matching row 47's `"a/b<1.5"` label/threshold exactly. The contraction-joint check (row 39) is silently using the wrong (looser) threshold, or the label is stale.
4. **`γ`/`ψ1` absolute references for M/N,S/T columns point at L/R column** (e.g. `M8=M5*$L$6`, not `$M$6`): harmless only because γ/ψ1 values are identical across centro/bordo/spigolo in this workbook; would silently misapply the centro factor if a user ever set position-specific γ/ψ1.
5. **`Eisenman` table is dead data**: no formula in `carichi_distribuiti_concentrati` references the `Eisenman` sheet; its role (multi-wheel superposition) must be inferred from context, not verified from the workbook.
6. **Materiali `C16` validation reference doesn't resolve inside `Materiali`** (sheet only has 10 data rows): the dropdown annotation likely targets the main sheet's `C4`/`C18`, but the recorded address is unexplained — treat CLS/steel enums as coming from `Materiali!A2:A10`/`E2` by inspection, not by trusting the literal `C16` address.

## Golden test case

### Base (`pav-fondazione-materiali`)
CLS=C25/30, γc=1.5, ν=0.2, acciaio=B450C, γs=1.15, sottofondo="materiale di riporto costipato", h=200mm, c=30mm
→ Rck=30, fck=25, fcd=14.1667, fcm=33, fctm=2.60682, fcfm=3.12819, fcfk=2.18973, fcfd=1.45982, Ecm=31475.8, fyk=450, fyd=391.304, kT=0.06, d=170, λ=0.000919499, W=6.66667e6, l=776.901, k=2, vmin=0.494975, v=0.54

### `pav-carichi-distribuiti`
Input: G=0 daN/m², Q=2600 daN/m², γG=1.3, γQ=1.5, ψ1=0.9, ø=8mm, S=200mm
Output: qSLU=39 kN/m², qSLE,f=23.4 kN/m², M_SLU(sup/inf)=7758.68/7435.78 Nmm/m, M_SLE,f=4655.21/4461.47, σc,max=1.1638/1.11537 MPa, TL(stress)=0.531482/0.764045, σc,t=0.698281/0.669221 MPa, TL(crack)=0.32144/0.308063, As=251.327 mm²/m, Mrd=15046.9 Nmm/m, TL(rebar)=0.515634/0.494175 → all PASS

### `pav-carichi-concentrati` — "ruota motrice" (K-block), P=15.5kN, bx=500, by=100mm
2 representative rows (centro, spigolo) + note bordo:
- centro: P_SLU=23.25kN, b=120.861mm, σc,max=0.789861 MPa, TL(stress)=0.541068, VEd=26.7375kN, u0=1200mm, vEd0=0.131066 MPa, TL(punch,u0)=0.0342657, u1=3336.28mm, vEd1=0.0471421 MPa, TL(punch,u1)=0.0952414, σc,t=0.473917 MPa, TL(crack)=0.218158, M_SLU=5265.74 Nmm/m, TL(rebar)=0.349956
- spigolo: σc,max=1.02311 MPa, TL(stress)=0.70085, VEd=34.875kN, u1=1228.32mm, vEd1=0.167015 MPa, TL(punch,u1)=0.33742, σc,t=0.613868 MPa, TL(crack)=0.282583, M_SLU=6820.76 Nmm/m, TL(rebar)=0.453301
- bordo (aggregate check, uses h not d bug): u1=1956.64mm, vEd1=0.097857 MPa, TL(punch,u1)=0.197701
All TL ≤1 → PASS for this case.

### `pav-giunti`
Input: a'=20m, b'=18m, a=30.9m, b=21.2m, α=1e-5, ΔT=30°C, h=200mm
Output: ratio1=1.11111→OK, Lmax=460cm, t_iso=40mm, ratio2=1.45755→OK, sp=9.27mm
