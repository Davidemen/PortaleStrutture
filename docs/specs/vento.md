# Vento — Wind Load Spec

Two tools: **A) vento** (wind pressure per height, NTC2018 §3.3 / DM14/01/2018) and **B) vento-cpe** (external pressure coeff. cpe, rectangular buildings, Circ. C3.3.8.1).

## A) Tool: vento (sheet `Vento`, lookup sheets `Tabelle`, `Comuni`)

### 1. Purpose + code refs
Computes basic/reference wind velocity, kinetic reference pressure `qb`, exposure coefficient `ce(z)`, and wind pressure profile `qz` vs height, per NTC2018 §3.3 (DM14/01/2018). Return-period correction per Circ. NTC2019 C3.3.2. Exposure coeff. formula per §3.3.7.

### 2. Inputs
| cell | symbol | meaning | unit | type/enum/range | cached example |
|---|---|---|---|---|---|
| Vento!H4 | comune | municipality name | text | free text, must exist in `Comuni!D` | "Milano" |
| Vento!H8 | as | site altitude a.s.l. | m | number (warns if >1500) | 120 |
| Vento!H13 | TR | return period | years | number | 50 |
| Vento!H28 | — classe rugosità | terrain roughness class | enum | A/B/C/D | "C" |
| Vento!H29 | categoria | exposure category | enum | I/II/III/IV/V | "II" |
| Vento!H33 | ct | topography coefficient | – | number, default 1 | 1 |
| Vento!H34 | H | max building height | m | number | 60 |
| Tabelle!M1 | n. sezioni | number of height subdivisions for profile table | – | integer, default 1000 | 1000 |

Note: H28 (roughness class) is a UI input but **not referenced by any formula** — dead input (see §7).

### 3. Outputs
| cell | symbol | meaning | unit | cached value |
|---|---|---|---|---|
| Vento!H5 | provincia | province (lookup) | text | "Milano" |
| Vento!H6 | regione | region (lookup) | text | "Lombardia" |
| Vento!H7 | zona | wind zone (1-9) | – | 1 |
| Vento!B10 | vb,0 | base wind velocity | m/s | 25 |
| Vento!E10 | a0 | zone altitude threshold | m | 1000 |
| Vento!H10 | ka | altitude coefficient | 1/s | 0.01 |
| Vento!H12 | vref | reference velocity (TR=50y) | m/s | 25 |
| Vento!H14 | aR | return-period multiplier | – | 1.00073 |
| Vento!H15 | vR(TR) | reference velocity for TR | m/s | 25 |
| Vento!B31 | kr | terrain factor | – | 0.19 |
| Vento!E31 | z0 | roughness length | m | 0.05 |
| Vento!H31 | zmin | minimum height | m | 4 |
| Vento!H36 | qb | reference kinetic pressure | kN/m² | 0.390625 |
| Vento!H37 | ce(z) | exposure coeff. at z=H | – (mislabeled "m") | 3.60638 |
| Vento!H8 check | L8 | altitude warning if as>1500 | text | "" (pass) |
| Tabelle!M1:P1004 | vm,vp,cev,qz | wind speed/pressure profile per height section | m/s, m/s, –, kN/m² | qz(z=60)=1.409 (Vento!H45 label) |
| Tabelle!N1 (M1) | max sections warning | if >1000 sections | text | "" (pass) |

Design pressure at height z: `qz(z) = qb · ce(z) · cp · cd` — cp comes from vento-cpe tool; cd (dynamic coeff.) not computed here (implicitly =1, per label "(con Cp=1)").

### 4. Calculation steps (dependency order)
1. Province/Region lookup: `[H5]=INDEX(Comuni!A:G, MATCH(H4,Comuni!D:D), MATCH("Provincia",Comuni!A1:G1))`; `[H6]` analogous for "Regione" col.
2. Zone: `[H7] zona = VLOOKUP(H5, Comuni!D:J, 3, FALSE)` — **note: VLOOKUP keyed on H5 (province name) against col D (Comune name)**, col offset 3 = col F "Vento" zone. See bug §7.
3. Zone table lookup (Tabelle!A3:D11, key=zona): `[B10] vb,0`, `[E10] a0`, `[H10] ka = VLOOKUP(H7, Tabelle!A3:D11, {2,3,4}, FALSE)`.
4. `[H12] vref = IF(as>a0, vb0 + ka·(as−a0), vb0)` — altitude correction, §3.3.1.
5. `[H14] aR = 0.75·sqrt(1 − 0.2·ln(−ln(1 − 1/TR)))` — Gumbel return-period factor, Circ. C3.3.2.
6. `[H15] vR(TR) = vref · sqrt( (1−0.2·ln(−ln(1−1/TR))) / (1−0.2·ln(−ln(0.98))) )` — normalizes aR(TR) against aR(TR=50) baked as `ln(-ln(0.98))`≈aR at TR=50.
7. Exposure-category table lookup (Tabelle!A17:D21, key=categoria I..V): `[B31] kr`, `[E31] z0`, `[H31] zmin = VLOOKUP(H29, Tabelle!A17:D21, {2,3,4}, FALSE)`.
8. `[H36] qb = 0.5·ρ·vR²/1000` (ρ=Vento!H35=1.25 kg/m³; /1000 converts Pa→kN/m²).
9. `[H37] ce(z=H) `: if H34<zmin: `ce = kr²·ct·ln(H/z0)·(7+ct·ln(H/z0))`; else same with `ln(zmin/z0)` (i.e. formula picks the **smaller** of H34,zmin — effectively caps profile at zmin from below; label unit "m" is wrong, ce is dimensionless).
10. Profile table `Tabelle!K4:Q1004` (fill-down, 1000 rows, index n=0..1000, L=height coordinate):
    - `L[n] = H34/M1 · K[n]` — height at section n = (building height / n.sections)·n.
    - `M[n] vm(z) = IF(L<z0_min(E31), 0, kr·ct·ln(L/z0)·vR)` — mean wind velocity at height L (wind profile law, uses `ct` twice by mistake: `H33*LN(...)*H15` → this omits kr on the ln argument scaling but multiplies by kr via B31? Actually formula is `B31*H33*LN(L/E31)*H15` = kr·ct·ln(L/z0)·vR).
    - `O[n] ce(L) = IF(L<zmin, ce(zmin-formula), ce(L-formula))` — same exposure-coeff formula as step 9 evaluated at L instead of H34, i.e. the per-row `ce(z)`.
    - `N[n] vp(z) = O[n]·vR` — peak velocity (labeled vp but is `ce·vR`, not gust velocity in classic sense — used only as intermediate for qz).
    - `P[n] qz(z) = 0.5·ρ·N[n]²/1000` — wind pressure at height L, kN/m² (this is `qb·ce²`-like via N, since N=ce·vR ⇒ P=0.5·ρ·ce²·vR² = qb·ce²... but note H37 defines ce differently — see §7 discrepancy).
    - Last row (K=1000/1005) special-cased: N=Q=P=0 (sentinel terminator row).
11. Display strings: `[G40]` states pressure below zmin is constant = `Tabelle!R4` (=ROUND(P4,3)=0.703 kN/m², Cp=1 assumed); `[G45]` states pressure at z=H34 = `ROUND(H36*H37,3)` = 0.5·ρ·vR²/1000 · ce(H) = qb·ce(H) = 1.409 kN/m² (Cp=1 assumed).

### 5. Lookup tables
- `Tabelle!A3:D11` — wind zone (1-9) → vb,0 [m/s], a0 [m], ka [1/s]. Key=zone number, exact match (VLOOKUP FALSE).
- `Tabelle!A17:D21` — exposure category (I-V) → kr, z0 [m], zmin [m]. Exact match.
- `Comuni!A1:G8102` — municipality DB: Regione, Provincia, Codice Istat, Comune, Sismica(zone), Vento(zone 1-9), Neve(category). Key=Comune (col D) for province/region INDEX/MATCH; key=Provincia (col D again, reused) for zone VLOOKUP — see bug.
- `Tabelle!K4:Q1005` — 1000-row fill-down profile table, index K=0..1000 (n.sections), row n = height fraction n/1000 of H34.

### 6. Hardcoded constants
- `ρ = 1.25 kg/m³` (Vento!H35) — air density, §3.3.6.
- `0.98` in aR baseline formula (Vento!H15) — represents `1 − 1/TR` for TR=50 (baseline for normalization), Circ. C3.3.2.
- `/1000` in qb, qz formulas — Pa → kN/m² conversion.
- `1500 m` altitude warning threshold (Vento!L8) — §3.3.1 note.
- `M1=1000` sections default (Tabelle!M1) — arbitrary resolution, not code-mandated; warns if user sets >1000.
- Cp=1 assumed in display strings G40/G45 — pressure coeff. deferred to vento-cpe tool.

### 7. Suspected bugs / fragile spots
- **Zone lookup double-keys on H5 (Provincia), not H4 (Comune)** (Vento!H7: `VLOOKUP(H5,Comuni!D:J,3,FALSE)`), while col D of Comuni is "Comune" not "Provincia". Since many municipalities share a province name, this returns the zone of **whatever row happens to match province-as-if-it-were-a-comune-name** — i.e., it accidentally works only when a municipality shares its name with its own province (e.g. "Milano" comune = "Milano" provincia), else returns the zone of an unrelated/first-matching row or #N/A. Fragile — verify before reuse; likely a copy-paste bug (should key on H4).
- **H28 (Classe di rugosità) is entirely unused** — no formula references it; dead input, possibly vestigial from an older NTC version or the field is meant for user reference only.
- **ce(z) label unit "m" (Vento!I37)** is wrong — ce is dimensionless [-], not meters.
- **Vento!H15 label formula concatenates H13 into text** — cosmetic only, not a calc bug.
- **Row 1005 sentinel** (Tabelle N1005=0,O1005=0,P1005=0 hardcoded, not formulas) breaks the fill-down pattern; if `M1` (n.sections) changes, this hardcoded terminator row does NOT move — the table may silently truncate/extend incorrectly for non-default section counts.
- **qz(z) via row P uses N² (=ce(L)·vR)² while H37/H45 uses qb·ce(H) directly** — two different formulas for pressure at the same conceptual point (H34): `P[1004]=0.5·ρ·(ce·vR)²/1000` vs `H45=qb·ce(H34)=0.5·ρ·vR²/1000·ce(H34)`. These are algebraically equal only if ce as computed in O-column equals ce² relationship... actually `P=0.5ρ(ce·vR)²=0.5ρ·vR²·ce²=qb·ce²`, but `H45=qb·ce`. **This is a real inconsistency**: table pressure profile scales as ce², displayed final-height pressure scales as ce¹. Needs verification against golden values below (P1004=1.409? check).

### 8. Golden test case
```
Inputs: H4="Milano", H8=120, H13=50, H28="C", H29="II", H33=1, H34=60, Tabelle!M1=1000
H5="Milano", H6="Lombardia", H7=1
B10(vb0)=25, E10(a0)=1000, H10(ka)=0.01
H12(vref)=25, H14(aR)=1.00073, H15(vR)=25
B31(kr)=0.19, E31(z0)=0.05, H31(zmin)=4
H36(qb)=0.390625 kN/m2
H37(ce@H=60m)=3.60638
H45 display pressure @60m = ROUND(qb*ce,3) = 1.409 kN/m2
Tabelle row @L=4m(zmin, n≈67): P≈0.703 kN/m2 (per G40 label, Cp=1)
Tabelle row n=1000 (L=60m): N(vp)=47.4762 m/s, P(qz)=1.40874 kN/m2
```
Note: P1004=1.40874 ≈ H45=1.409 (round) — so despite the ce² vs ce concern in §7, values coincide because `O1004` (ce at L=60) computed via the row-formula equals `H37` (ce at H=60) exactly (both hit the same branch, same inputs), and `N=O·vR`, `P=0.5ρN²`. Re-deriving: `P=0.5ρ(O·vR)²=0.5ρ·vR²·O²`; but `H36*H37=0.5ρvR²·H37`. For P≈H45 numerically we'd need O²≈H37, i.e. O≈√3.60638≈1.899 — **and indeed O1004(cev)=1.89905** in the CSV! So O-column "cev" is NOT the same ce as H37; it's `sqrt(ce)`-like (actually it equals kr·sqrt(ct·ln(...)·(7+...))-form without squaring — i.e. O is literally the sqrt formula, consistent, and H37 uses the squared form `kr²·...`). So **no bug**: O(cev) and H37(ce) are different intentional quantities (velocity-multiplier vs pressure-multiplier); retract inconsistency claim — keep only as a naming/formula-duplication fragility note (two nearly-identical LN expressions maintained in two places, Vento!H37 and Tabelle!O-col, risk of divergent edits).

## B) Tool: vento-cpe (sheet `Foglio1`) — Circ. NTC C3.3.8.1, rectangular-plan buildings

### 1. Purpose
External pressure coefficients cpe for windward/side/leeward faces of rectangular-plan buildings, both wind directions, per h/d ratio.

### 2. Inputs
| cell | symbol | meaning | unit | type | example |
|---|---|---|---|---|---|
| D6 | b | plan width, dir 1 | m | number | 15 |
| D7 | d | plan depth, dir 1 | m | number | 12 |
| D8 | h | building height | m | number | 9 |

E6/E7 auto-swap b,d for direction 2 (`E6=D7`, `E7=D6`).

### 3. Outputs
| cell | symbol | meaning | value (dir1/dir2) |
|---|---|---|---|
| D9/E9 | h/d | slenderness ratio | 0.75 / 0.6 |
| B10 | classification | "EDIFICIO TOZZO" (squat) if both ≤5, "SNELLO" (slender) if both >5, else per-direction | "EDIFICIO TOZZO" |
| D13/E13 | cpe windward | 0.775 / 0.76 |
| D14/E14 | cpe side | -0.9 / -0.9 |
| D15/E15 | cpe leeward | -0.45 / -0.42 |

### 4. Calculation steps
1. `h/d [D9,E9] = h/d`.
2. Classification `[B10]`: slender if h/d>5 both dirs; squat if ≤5 both; mixed otherwise (per-direction label).
3. `cpe,windward [D13] = IF(h/d>5,"ND", IF(h/d≤1, 0.7+0.1·(h/d), 0.8))` — piecewise linear 0.7→0.8 for h/d∈[0,1], capped 0.8 for h/d∈(1,5], "ND" (not defined) above 5.
4. `cpe,side [D14] = IF(h/d>5,"ND", IF(h/d≤0.5, −0.5−0.8·(h/d), −0.9))`.
5. `cpe,leeward [D15] = IF(h/d>5,"ND", IF(h/d≤1, −0.3−0.2·(h/d), −0.5−0.05·(h/d−1)))`.
6. Reference table rows 18-21 (h/d = 0, 0.5, 1, 5) tabulate the same 3 formulas for documentation/interpolation reference — redundant with steps 3-5, not used elsewhere.

### 5. Lookup tables
None (pure piecewise formulas); rows 18-21 are a printed reference table, not looked up by formula.

### 6. Hardcoded constants
- `0.7, 0.1, 0.8` — windward cpe piecewise coefficients, Circ. C3.3.8.1 Fig./Tab.
- `-0.5, -0.8, -0.9` — side cpe.
- `-0.3, -0.2, -0.5, -0.05` — leeward cpe.
- Breakpoints `h/d ≤1` (windward/leeward), `h/d≤0.5` (side), `h/d>5` (ND / slender-building exclusion) — from code table.

### 7. Suspected bugs
- `[B10]` classification formula has no final ELSE for the "both ≤5 but not both, not... " branch structure — actually IF/IF/IF/IF with no final else: if D9≤5 and E9≤5 → tozzo; elif D9>5 → snello dir1 (regardless of E9); elif E9>5 → snello dir2; else (D9≤5,E9>5 already caught, D9>5,E9≤5 already caught) → **FALSE returned as blank/0** for unreachable case — logic looks complete via elif chain, no bug found on inspection.
- `[D9]=D8/D7` and `[E9]=E8/E7` — confirmed correct (h over d, using swapped d for dir2).
- No bugs confirmed; formulas are straightforward piecewise linear per code table.

### 8. Golden test case
```
Inputs: D6(b)=15, D7(d)=12, D8(h)=9 → E6=12, E7=15, E8=9
D9(h/d dir1)=0.75, E9(h/d dir2)=0.6
B10="EDIFICIO TOZZO"
D13(cpe windward dir1)=0.775, E13(cpe windward dir2)=0.76
D14(cpe side dir1)=-0.9, E14(cpe side dir2)=-0.9
D15(cpe leeward dir1)=-0.45, E15(cpe leeward dir2)=-0.42
```
