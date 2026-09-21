# Cedimenti — Edometrico (Oedometric Settlement) — Implementation Spec

Sheet `Edometrico` (workbook geo-cedimenti). Computes the settlement of a flexible
rectangular foundation by the oedometric (Terzaghi) method: layered soil profile,
stress increase with depth under the loaded area, per-layer strain via Eed, summed
to a significant depth. Governing refs: Terzaghi 1D consolidation/oedometric method
(NTC 2018 §6.2.2 / Circolare 2019 C6.2.2 "?" — no explicit clause numbers appear in
the sheet), classical Boussinesq/Newmark rectangular-load stress solution.

Geometry/loads are **imported by formula** from sheet `Elastico_centrale_Newmark`
(out of scope — not read here): B[cm], L[cm], q[kg/cmq] are the footing width,
length and applied contact pressure already computed there. The 5-layer soil table
(from/to/Eed) is likewise imported from that sheet's rows 7-11.

## Tool: `geo-cedimenti-edometrico` — layered oedometric settlement

### Purpose
For a rectangular footing (B×L) under net pressure q', discretizes the soil below
in 10 cm slices down to z=5000 cm, computes at each slice: the load-induced stress
increase Δσv,q (approximate rectangular-load formula), the buoyant effective
overburden increase Δσ'v, the layer's oedometric modulus Eed(z), and the oedometric
strain increment ΔH,i = Δz·Δσv,q/Eed. Sums increments up to a user-set "critical
depth" Z,crit (nominally where Δσv,q = 0.1·Δσ'v, the classical significant-depth
criterion) to get the total settlement wed(f).

### Inputs — scalars
| cell | symbol | meaning | unit | type | cached example |
|---|---|---|---|---|---|
| B1 | B | Footing width, `=Elastico_centrale_Newmark!D1` | cm | formula (external input) | 350 |
| B2 | L | Footing length, `=Elastico_centrale_Newmark!D2` | cm | formula (external input) | 500 |
| B3 | γ | Soil unit weight | kg/mc | number, unlocked/user input | 1800 |
| B11 | q | Applied contact pressure, `=Elastico_centrale_Newmark!D3` | kg/cmq | formula (external input) | 0.5 |
| B8 | (unlabeled) | Foundation embedment depth used only in q' formula; no row label in this sheet — likely "depth of overburden removed", in **meters** given the ×0.0001 unit-conversion factor used against it | m "?" | number, blank/0 in cached example | (blank → 0) |
| B12 | q' | Net design pressure = q − γ·B8/10000 | kg/cmq | formula | 0.5 |
| B18 | Z,crit | Cutoff depth for the settlement sum ("Z per cui Δσv,q = 0.1·Δσ'v", D18) | cm | number, unlocked/user input — **not auto-computed**, see §7 | 10000 |

### Inputs — soil layer table (rows 5-9, max 5 layers)
One row = one soil layer, ordered by depth, contiguous (`to[i]` should equal
`from[i+1]`). All three columns are formulas pulling from `Elastico_centrale_Newmark`
(sheet out of scope) — treat as external table input, not directly editable here.
| col | symbol | meaning | unit | source (row i → Newmark row i+2) |
|---|---|---|---|---|
| C5:C9 | from | Layer top depth | cm | `=Elastico_centrale_Newmark!D7:D11` |
| D5:D9 | to | Layer bottom depth | cm | `=Elastico_centrale_Newmark!E7:E11` |
| E5:E9 | Eed | Oedometric modulus | kg/cmq | `=Elastico_centrale_Newmark!F7:F11` |

Cached example (5 layers): (0,370,56.0844), (370,470,71.3801), (470,550,91.7745),
(550,3150,71.3801), (3150,11890,71.3801).

### Inputs — depth table (fill-down, rows 3-503, 501 rows)
One row = one 10 cm depth slice. **Only column G is user/geometry-independent
fill-down data (z = 0, 10, 20, …, 5000 cm, step hardcoded at 10 cm)**; all other
columns (H,I,J,K,L,M,N,P,Q,R,T) are fill-down **formulas**, no user data. Full
values in `edometrico.csv` (503 rows incl. 2 header rows).
| col | symbol | meaning | unit |
|---|---|---|---|
| G | z | Depth below foundation base | cm |
| H | Δσv,q | Load-induced vertical stress increase at depth z | kg/cmq |
| I | Δσ'v | Buoyant effective-overburden stress increase at depth z | kg/cmq |
| J | Eed(z) | Layer oedometric modulus applicable at depth z | kg/cmq |
| K | ΔH,i | Settlement increment of the slice | cm |
| L | ΣΔH,i | Running cumulative settlement, unconditional | cm |
| M | ΣΔH,i (capped) | Running cumulative settlement, reset to 0 once z ≥ Z,crit | cm |
| N | Δσv,q+Δσ'v | Sum, display only, unused downstream | kg/cmq |
| P,Q,R | R1,R2,R3 | `sqrt(L²+z²)`, `sqrt(B²+z²)`, `sqrt(B²+L²+z²)` | cm |
| T | (unlabeled) | Exact Newmark corner-stress factor using q', B, L, z — **reference/verification only, not used by K/L/M** | kg/cmq |

### Outputs
| cell | symbol | meaning | unit | cached |
|---|---|---|---|---|
| B15 | wed(f) | Total oedometric settlement = `MAX(M3:M503)` | cm | 2.9958 |

No explicit pass/fail check cell exists in this sheet; wed(f) is compared by the
engineer against a project-specific admissible settlement (external to this sheet).

### Calculation steps (dependency order)
1. `B12[q'] = B11[q] − B3[γ]·0.0001·B8` (0.0001 = m→ assumed conversion, see input note "?").
2. For each depth row i (z_i = G_i, z_0=0, step 10 cm, i=0..500):
   a. `H_i[Δσv,q] = q'·B·L / ((L+z_i)·(B+z_i))` — approximate stress under center of
      a flexible rectangular loaded area (not the exact Boussinesq/Newmark integral;
      that is computed separately in column T for comparison only).
   b. `I_i[Δσ'v] = (γ−1000)·1e-6·z_i` — buoyant unit weight (γ−γw), γw=1000 kg/m³
      baked in, converted kg/m³·cm → kg/cm² via the 1e-6 factor (1 m³=1e6 cm³);
      implicitly assumes water table at z=0.
   c. `J_i[Eed] = ` piecewise lookup on the 5-layer table: first layer test uses
      `z_i ≥ from_1 AND z_i ≤ to_1` (only row for z=0, i.e. i=0, uses `≥`); layers
      2-5 use `z_i > from_k AND z_i ≤ to_k`; falls to 0 if z_i exceeds all layers
      (→ divide-by-zero risk, see §7).
   d. `K_0 = 0` (degenerate: `z_0·H_0/J_0` with z_0=0). `K_i = (z_i − z_{i-1})·H_i/J_i`
      for i≥1 — oedometric strain: Δz·Δσv,q/Eed.
   e. `L_i = L_{i-1} + K_i` (L_0 = K_0 = 0) — unconditional cumulative sum.
   f. `M_i = z_i < Z,crit ? K_i + M_{i-1} : 0` — mirrors L while z_i<Z,crit, then
      drops to 0 past the cutoff (relies on L/M being monotonically increasing up
      to the cutoff so `MAX(M)` recovers the cumulative value at cutoff — see §7).
   g. `P_i,Q_i,R_i` per formulas above; `T_i` = classical Newmark corner-stress
      factor (informational, not consumed by e/f).
3. `B15[wed(f)] = MAX(M3:M503)`.

### Lookup tables
- Soil layer table (C5:E9 → E), key = depth z, 5 contiguous bands, exact
  band-membership match (no interpolation), see input table above.

### Hardcoded constants
- Depth-table range: 0–5000 cm in 10 cm steps (501 points) — fixed, not derived
  from footing size or layer table extent; if the true significant depth exceeds
  5000 cm, wed(f) is truncated silently.
- γw = 1000 kg/m³ (baked into `I` formula, buoyant/submerged assumption, water
  table at foundation base level).
- Unit-conversion factors: `1e-6` (kg/m³·cm → kg/cm²) in `I`; `1e-4` (`0.0001`) in
  `B12` formula against B8.
- Depth-table max 5 soil layers (fixed 5-row IF chain in J).

### Suspected spreadsheet bugs / fragile spots
1. **Orphaned Cardano cubic solver (rows 24-28, cols A/B).** Cells `p[B24]`,
   `q[B25]`, `u[B27]`, `v[B28]` implement Cardano's formula for the depressed
   cubic `t³+pt+q=0` derived from `Δσv,q(z) = 0.1·Δσ'v(z)`, i.e. solving exactly
   for the "Z,crit" depth documented in D18. But **no cell ever computes the final
   root `z = u+v−(B1+B2)/3`**, and B18 is a plain hardcoded constant (10000 in the
   cached file), not a formula. So the auto-derivation is dead code; the user must
   apparently read u/v and finish the arithmetic by hand, or (as cached) leave
   B18 at a value larger than the depth table's 5000 cm max, which disables the
   cutoff entirely (M≡L for the whole table) and just sums to 50 m depth. Verified:
   with cached B1=350,B2=500,B3=1800,B12=0.5, `u+v−(B1+B2)/3 = 1031.6+21.2722−283.333
   = 769.539 cm`, which does solve H(z)=0.1·I(z) (checked numerically). A faithful
   reimplementation should compute this root directly (closed form, no need to
   replicate the orphaned intermediate cells) and use it as Z,crit unless the user
   overrides it.
2. **Divide-by-zero if layers don't cover the full 0-5000 cm range.** `J_i` falls
   back to 0 past the last layer's `to`, making `K_i = Δz·H_i/0` blow up. Cached
   layer table happens to reach 11890 cm > 5000, masking this. A reimplementation
   must guard: extend the last layer to depth table max, or raise a validation
   error if the layer table doesn't cover [0, table max].
3. **B8's role is unlabeled** (no `A8` cell) — only inferred from its use in the
   `q'` formula and the `×0.0001` unit hint that it's meters. Confirm with the
   Elastico_centrale_Newmark sheet or ask the user before hardcoding a meaning;
   treat as "foundation depth (embedment) — reduces q by γ·D" pending confirmation.
4. **Row-0 boundary special case**: only the first layer's lower-bound test in row
   3 (z=0) uses `≥` (`G3>=$C$5`) while every other row/layer uses strict `>`. This
   only matters if a layer's `from` is queried at exactly z=0; keep the `[0,to_1]`
   inclusive-at-both-ends behavior for z=0 only, `(from,to]` elsewhere.
5. **N column (Δσv,q+Δσ'v) and T/P/Q/R columns** are computed but never consumed
   by the settlement result; safe to omit from a reimplementation unless exposing
   them as diagnostic output is wanted.

### Golden test case
Inputs: B[B1]=350 cm, L[B2]=500 cm, γ[B3]=1800 kg/mc, q[B11]=0.5 kg/cmq, B8=0 (blank),
Z,crit[B18]=10000 cm (i.e. disabled/no-op cutoff for this run), layers=
[(0,370,56.0844),(370,470,71.3801),(470,550,91.7745),(550,3150,71.3801),(3150,11890,71.3801)].
q'[B12] = 0.5.

Representative rows:
- z=0 (row3): Δσv,q=0.5, Δσ'v=0, Eed=56.0844, ΔH,i=0, ΣΔH,i=0
- z=10 (row4): Δσv,q=0.47658, Δσ'v=0.008, Eed=56.0844, ΔH,i=0.0849754, ΣΔH,i=0.0849754
- z=1970 (row200 of csv, mid-table): Δσv,q=0.0152694, Δσ'v=1.576, Eed=71.3801, ΔH,i=0.00213917, ΣΔH,i=2.71064
- z=5000 (row503, last): Δσv,q=0.00297366, Δσ'v=4.0, Eed=71.3801, ΔH,i=0.000416595, ΣΔH,i=2.9958

Aggregate output: `wed(f)[B15] = 2.9958 cm` (= L503/M503 since Z,crit was left
disabled in this cached run).

Cross-check value (not wired in sheet, see bug #1): critical depth root where
Δσv,q=0.1·Δσ'v ≈ 769.539 cm; cumulative settlement at that depth ≈ interpolate
between row ~80 (z=770) values, i.e. considerably less than the full 2.9958 cm if
the cutoff were actually applied.
