# Phase 4 architecture — RC section engine (M-N) and bearing capacity

No spreadsheet exists for either: there is NO Excel oracle and no `legacy_compat` mode. Correctness rests on
closed forms, published benchmarks, invariants and an engineering review. Follow `docs/BUILD_CONTRACT.md`
(modularity, frozen models, TDD, UI hints, sketches, Windows + macOS).

## A. `strutture.shared.sezione_ca` — generic RC section engine (pure, no Tool)
**Inputs.** Concrete outline = polygon (vertices in mm, counter-clockwise, simple, may be non-convex: T, L, U,
wall with boundary elements; circle = regular 48-gon preset); optional holes later. Bars = tuple of (x_mm, y_mm,
ø_mm). Materials from `shared.materials` (fcd, fyd, Es; εc2, εcu2, εc3, εcu3 for ≤ C50/60 per NTC 2018
§4.1.2.1.2.1; εud = 0.9·εuk with εuk = 75‰ for B450C, or unlimited strain for the elastic-perfectly-plastic law).
**Constitutive laws** (`leggi.py`): concrete parabola-rectangle (default) and rectangular stress block (0.8x,
η = 1) — tension ignored; steel elastic-perfectly-plastic (default) or bilinear with hardening k = ft/fy.
**Strain plane** ε(x, y) = ε0 + κx·y − κy·x (sign convention documented once: compression negative inside the
engine, results reported with N > 0 compression, M > 0 tension at the bottom fibre — state it in every result).
**Integration** (`integrazione.py`): concrete by polygon clipping to the compressed zone, then strips
perpendicular to the neutral axis (adaptive: n strips until ΔN, ΔM < 1e-4 relative; default 200) — exact area
per strip from the clipped polygon, stress at the strip centroid with Simpson over the parabola; bars as point
areas with the displaced concrete stress subtracted. No numpy: tuples + comprehensions; one evaluation < 2 ms.
**Ultimate states** (`stati_ultimi.py`): for a neutral-axis angle θ, sweep the classic pivot domains: pivot A
(steel at εud), pivot B (concrete at εcu2), pivot C (εc2 at depth (1−εc2/εcu2)·h) from pure tension to pure
compression; each state -> (N, Mx, My).
**Domains.** `dominio_nm(sezione, asse: "x"|"y", n_punti=72) -> tuple[PuntoDominio, ...]` (closed curve);
`m_rd(sezione, n_ed_kN, asse) -> MRd±` by interpolation on the domain + bisection refinement on the pivot
parameter; `dominio_biassiale(sezione, n_ed_kN, n_angoli=36) -> tuple[(Mx, My)]` (the Mx–My interaction curve at
constant N, neutral-axis angle sweep with the inner loop solving N = N_Ed); `verifica(sezione, N, Mx, My) ->
{rapporto, dentro}` where rapporto = |M_Ed| / |M_Rd(N, direction of M_Ed)| along the ray from the origin.
**Presets** (`forme.py`): rettangolo(b, h), cerchio(D), T(bf, hf, bw, h), L, parete(lw, tw, elementi di
estremità), each returning the polygon; bar layouts: file superiore/inferiore, perimetrale (n per lato),
circolare (n, copriferro).
**Verification plan (tests are the deliverable):**
1. Closed forms: pure compression N = fcd·Ac + fyd·As; pure tension N = −fyd·As; rectangular section in pure
   bending equals the stress-block closed form AND the existing `ca-trave-rettangolare` M_Rd within 0.5 %
   (parabola-rectangle vs block differ slightly — assert both laws separately); balanced point ξ = εcu/(εcu+εyd).
2. Invariants: domain is convex and contains the origin; symmetric section + symmetric bars -> domain symmetric
   about the N axis; rotating the whole section by 90° swaps Mx/My; scaling all dimensions by k scales N by k², M
   by k³; refining strips changes results < 1e-3; circle-as-48-gon vs analytic segment areas < 0.2 %.
3. Benchmarks: two published worked examples with full data (choose ones you can reproduce exactly and cite the
   source in the test docstring); if a figure cannot be verified from first principles, do not use it.
4. Biaxial: for a square section with 4 corner bars the Mx–My curve is symmetric about the diagonal; at θ = 0/90°
   it reduces to the uniaxial values.

## B. Tools (package `strutture.members.ca_sezione_mn`)
- `ca-sezione-dominio-mn`: forma (rettangolare | circolare | a T | a L | parete | poligono libero), dimensions
  (conditional fields per forma), table `barre` (x, y, ø) OR a layout preset, materials, legge costitutiva,
  azioni (N_Ed, M_Ed,x, M_Ed,y as a TABLE of combinations via `shared.tabular`, ≤ 500 rows). Output: domain N–M
  for both axes (chart hints), M_Rd at each N_Ed, per-combination rapporto with envelope + governing row, checks on
  the envelope, sketch of the section with bars and the neutral axis of the governing combination.
- Chain (Phase 5): `provides: "mrd_kNm"` so `ca-pilastro-*` can take M_Rd instead of a typed value.

## C. `strutture.shared.capacita_portante` — bearing capacity [A: assumptions to confirm with the engineer]
EN 1997-1 Annex D (Brinch-Hansen form), as used with NTC 2018 §6.4.2.1:
- drained: q_lim = c'·Nc·bc·sc·ic + q'·Nq·bq·sq·iq + 0.5·γ'·B'·Nγ·bγ·sγ·iγ with Nq = e^{π tanφ'}·tan²(45°+φ'/2),
  Nc = (Nq−1)·cotφ', Nγ = 2·(Nq−1)·tanφ' (rough base); shape, load-inclination (m exponent by load direction) and
  base-inclination factors exactly as Annex D.4; effective area B' = B − 2e_B, L' = L − 2e_L;
- undrained: q_lim = (π+2)·cu·bc·sc·ic + q;
- water table: γ' below it, q' effective; optional depth factors OFF by default (Annex D has none) — expose as an
  advanced option (Hansen d-factors) with a warning;
- design: approach 2 (A1+M1+R3): characteristic φ'k, c'k, cu,k with γM = 1.0 and γR = 2.3 (static); seismic: γR
  = 2.3 with the option of the Paolucci–Pecker inertial reduction factors — advanced, default off, flagged "Da
  confermare". R_d = q_lim·A'/γR vs N_Ed (vertical component), per load combination.
**Integration:** `fond-plinto-isolato` gains an optional block "Terreno" (φ'k, c'k, cu,k, γ, falda, condizione
drenata/non drenata); when filled, the bearing resistance per combination comes from this module (per-row B', L',
inclination from V/N) instead of the typed value, which stays as a fallback; `muro-sostegno` replaces its
"non calcolata" warning with the same check on the base strip (per metre, L' -> ∞: shape factors = 1).
**Verification:** Nq/Nc/Nγ table values vs EN 1997-1 Annex D for φ' = 20/25/30/35/40°; hand-computed cases for
centred/eccentric/inclined loads; limits (φ' -> 0 gives the undrained form with cu = c'); monotonicity
(more eccentricity or inclination never increases R_d); Opus review against Annex D.
