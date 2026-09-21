# Divergences — `strutture.members.ca_travi` (tool `ca-trave-rettangolare`)

Golden case throughout: B=600mm, H=400mm, c=70mm, C35/45, RB500W, n1=5/ø1=20, staffe ø12/passo
115mm/2 bracci, VEd=138kN, MEd=318kNm, CD"B", MRc=350kNm (docs/specs/ca-travi.md §8).

## 1. `Z12` As,min uses z instead of d, and ftk instead of fyk

- **Cell**: `Travi sez. rettangolare!Z12` = `MAX(0.0013*H6*AM30, 0.26*H6*AM30*VLOOKUP(H9,Tabelle!M34:R41,6,FALSE)/Z7)`.
- **Sheet behaviour**: `AM30` is the lever arm `z=0.9*(H-c)` (297mm), not the effective depth
  `d=H-c` (330mm) that NTC2018 §4.1.6.1.1/EC2 9.2.1.1 specify. Worse, `Z7` (the divisor of the
  `0.26·fctm/fyk` term) is labelled "Tensione di rottura dell'acciaio" and holds **ftk** (650 MPa
  for RB500W), not fyk (500 MPa) — the formula divides by the wrong steel table column.
- **Fixed behaviour**: `armatura_limiti.area_minima_tesa_mm2` uses `d` and `fyk` when
  `legacy_compat=False`; `legacy_compat=True` reproduces `z`/`ftk` exactly.
- **Clause**: NTC2018 §4.1.6.1.1 (EC2 9.2.1.1).
- **Numeric impact on the golden case**: As,min 238.936 mm² (sheet) → 330.497 mm² (fixed, using
  the NTC2018-literal fctm=3.20996 MPa). As,o=1570.8 mm² still passes both ways.

## 2. `Z16`/`Y17` Ast,min staffe: NTC2018 §4.1.6.1.1's 1.5·b floor is mandatory, EC2 9.2.2(5) is an additional floor (corrected 2026-09-21)

- **Cell**: `Z16` = `1.5*H6` (mm²/m).
- **Sheet behaviour**: `Ast = 1.5·b` [mm²/m], independent of concrete/steel grade.
- **Previous (incorrect) fixed behaviour**: an earlier version of this port *replaced* the sheet's
  `1.5·b` with `ρw,min = 0.08·√fck/fyk` (EC2 9.2.2(5)) in `legacy_compat=False`, on the assumption
  that `1.5·b` was a pre-Eurocode rule of thumb. That assumption was wrong: NTC2018 §4.1.6.1.1
  states literally "staffe con sezione complessiva non inferiore ad Ast = 1,5 b mm²/m" — it is a
  mandatory NTC2018 floor, not a legacy convention, and replacing it lowered the required minimum
  stirrup area by 37% (900 → 567.94 mm²/m in the golden case) — a non-conservative regression.
- **Fixed behaviour (corrected)**: `armatura_limiti.limiti_staffe` now returns
  `max(1.5·b, ρw,min·b·1000)` when `legacy_compat=False`: the NTC2018 floor and the EC2 9.2.2(5)
  floor both apply, and the higher one governs. `legacy_compat=True` still reproduces the sheet's
  plain `1.5·b` exactly.
- **Clause**: NTC2018 §4.1.6.1.1 + EC2 9.2.2(5).
- **Numeric impact on the golden case**: Ast,min = 900 mm²/m in both modes (the NTC floor governs
  for this section); the EC2 floor only exceeds 1.5·b for unusually high fck / low fyk
  combinations (see `test_limiti_staffe_fixed_ec2_floor_governs_for_high_strength_low_grade_steel`
  in `tests/members/ca_travi/test_armatura_limiti.py`). Both floors pass against the actual
  1966.9 mm²/m of stirrups in the golden case.

## 3. `Z18`/`Y19` passo massimo staffe: 1000/3 mm and z instead of 330 mm and d

- **Cell**: `Z18` = `MIN(1000/3, 0.8*AM30)`.
- **Sheet behaviour**: caps the maximum stirrup spacing at 333.33mm (1/3 of a metre) using the
  lever arm z, instead of NTC2018 §4.1.6.1.1's `min(0.8·d, 330mm)`.
- **Fixed behaviour**: `armatura_limiti.limiti_staffe` returns `min(330, 0.8*d)` when
  `legacy_compat=False`.
- **Clause**: NTC2018 §4.1.6.1.1.
- **Numeric impact on the golden case**: passo massimo 237.6mm (sheet) → 264.0mm (fixed); the
  actual spacing (115mm) satisfies both.

## 4. `K60` passo massimo staffe zona critica degenerates to 0 — root cause differs from the spec write-up; also uses h instead of d (corrected 2026-09-21)

- **Cell**: `K60` = `IF(J58="CDA", MIN(H7/4, 24*MIN(H15), 175, 6*MIN(H12,H14)), MIN(H7/4, 24*MIN(H15), 225, 8*MIN(H12,H14)))`.
- **Sheet behaviour**: when the second longitudinal bar type is unused (`H14`=Ø2=0, as in the
  golden case where n2=0), `MIN(H12,H14)=0` forces the whole `MIN(...)` to 0mm, regardless of the
  real bar diameter (Ø1=20mm) or the real governing limit here. Note this is **not**
  `MIN(H15,H18)` (stirrup diameters) as `docs/specs/ca-travi.md`'s bug list (item 3) suspected — the actual cell
  formula only references `H15` (a single stirrup diameter), so the degenerate term is the bar
  diameter `MIN(H12,H14)`, not the stirrup diameter. Separately, `H7/4` uses the gross section
  height `h` (H7), not the effective depth `d` — NTC2018 §7.4.6.2.1 requires "un quarto
  dell'ALTEZZA UTILE della sezione trasversale", i.e. `d/4`, and since `h > d` always, `h/4` is
  strictly less conservative.
- **Fixed behaviour**: `capacity_design.passo_max_zona_critica_mm` excludes bar/stirrup types with
  a zero count from the `MIN` when `legacy_compat=False` (`_diametro_minimo_effettivo`), and uses
  `d_mm/4` instead of `h_mm/4` in the first `MIN` term when `legacy_compat=False`.
  `legacy_compat=True` still reproduces `h/4` and the degenerate bar-diameter term exactly.
- **Clause**: NTC2018 §7.4.6.2.1.
- **Numeric impact on the golden case**: p,max zona critica 0mm (sheet, degenerate) → 82.5mm
  (fixed, d/4=330/4 governs; using the previous h/4=100mm would have been 21% non-conservative).

## 5. `K81` VEd,max ignores `Lt` (luce della trave) — settled from the clause (corrected 2026-09-21)

- **Cell**: `K81` = `IF(J77="cdb",1,1.2)*K79*MIN(1,K78/K79)`; `K80` (Lt, luce della trave) is
  captured as an input right above this formula but is never referenced by it. The result is
  dimensionally a MOMENT (kNm) — `K79`=MRb (a moment) times a dimensionless amplification factor —
  yet the sheet compares it directly against `VRd` (a force, kN) in the "capacity design a
  taglio" check.
- **Previously** listed as "Da verificare" (uncertain reconstruction). **Settled**: NTC2018
  §7.4.4.1.1 gives the amplified end-moment demand `Mi,d = gammaRd*Mb,Rd,i*min(1,sum MC,Rd/sum Mb,Rd)` and
  the corresponding capacity-design shear `VEd = (Mi,d + Mj,d)/Lt`. The sheet supplies only one
  beam moment-capacity value (no separate end moments), so both ends are conservatively taken
  equal to the same `MRb`/`MRc` pair: `VEd = 2*gammaRd*MRb*min(1,MRc/MRb) / Lt`. `Lt` (`K80`,
  already a validated input on `TraveRettangolareInput.lt_m`) is now used.
- **Fixed behaviour**: `capacity_design.taglio_capacity_design_kN` implements the formula above
  when `legacy_compat=False`, returning a force in kN. `legacy_compat=True` still reproduces the
  sheet's `K81` exactly (a moment value, `Lt` unused) — golden/oracle tests are unchanged.
  The `LT_NON_UTILIZZATO_WARNING` in `tool.py` has been removed since `Lt` is now used in fixed
  mode (it remains inert only in `legacy_compat=True`, which is the sheet-reproduction mode by
  design, so no warning is needed there either).
- **Clause**: NTC2018 §7.4.4.1.1.
- **Numeric impact on the golden case** (MRb=207.01 kNm, MRc=350 kNm, CD"B", Lt=8m): VEd,max
  207.01 kN (sheet, dimensionally a moment) -> 51.75 kN (fixed, 2*1.0*207.01*1/8).

## 7. `Z42` σs SLS limit hardcoded to 360 MPa instead of 0.80·fyk

- **Cell**: `Z42` = `IF(Z41<360,"OK","NO")`.
- **Sheet behaviour**: the tensile-stress limit for the reinforcement in the rare combination
  (NTC2018 §4.1.2.2.5) is a literal `360`, correct only when the selected steel is B450C
  (fyk=450 → 0.80·450=360). For any other grade — e.g. the golden case's own RB500W (fyk=500) —
  the check silently uses the wrong limit. Contrast with `Z47`/`Y47` (concrete stress,
  quasi-permanente combination), which correctly recomputes `0.45·VLOOKUP(H9,...)` from the
  selected concrete class every time.
- **Fixed behaviour**: `sle_tensioni.limite_sigma_acciaio_MPa` returns `0.80·fyk_MPa` dynamically
  (from the selected `tipo_acciaio`) when `legacy_compat=False`; `legacy_compat=True` reproduces
  the hardcoded 360 MPa.
- **Clause**: NTC2018 §4.1.2.2.5.
- **Numeric impact on the golden case**: limite σs 360 MPa (sheet, RB500W fyk=500) → 400 MPa
  (fixed, 0.80·500). σs,rara=528.576 MPa exceeds both, so the pass/fail outcome ("NO") is
  unchanged for this particular case; the divergence matters for steel grades where 528.576 MPa
  would sit between the two limits, or for any grade with fyk far from 450 in general.

## 8. `AI54` crack-width table exact-match VLOOKUP raises `#N/A` for non-catalog bar diameters

- **Cell**: `AI54` = `VLOOKUP(Ømax, {Q67:R93|P67:R93|O67:R93}, ..., FALSE)` (exact match, per
  `Z54`'s w1/w2/w3 selection).
- **Sheet behaviour**: `Tab. C4.1.II` (Circolare 7/2019 C4.1.2.2.4.5) is tabulated for a discrete
  set of bar diameters that differs slightly per w-class (e.g. Ø=25mm is tabulated for w1/w2 but
  not for w3). Selecting a diameter/class combination not in the table returns `#N/A` instead of
  interpolating or rounding to the nearest tabulated diameter.
- **Fixed behaviour**: `strutture.shared.rebar_catalog.sigma_limit_by_diameter` interpolates
  linearly between the two bracketing diameters when `legacy_compat=False`;
  `fessurazione.verifica_fessurazione` re-raises the shared module's `KeyNotFound` as a
  `CalcError` (Italian message) in `legacy_compat=True` mode, matching the sheet's failure mode
  without silently returning a wrong number.
- **Clause**: NTC2018 §4.1.2.2.4 / Circolare 7/2019 C4.1.2.2.4.5, Tab. C4.1.II.
- **Numeric impact on the golden case**: none (Ø=20mm is an exact key in every w-class); see
  `tests/members/ca_travi/test_fessurazione.py` for a Ø=25mm/w3 case where legacy mode raises and
  fixed mode interpolates between 226.66 MPa (Ø24) and 219.999 MPa (Ø26).

## 9. Da verificare — `Y50`/`Y51`/`Y52` classe di fessurazione: user choice not cross-checked against Tab. 4.1.IV in the sheet

- The sheet lets the user pick `Z54` (classe di apertura fessura w1/w2/w3) completely
  independently of `Y50`/`Y51`/`Y52` (condizioni ambientali/combinazione/sensibilità
  dell'armatura), even though NTC2018 Tab. 4.1.IV maps that triple to a specific required class.
  Nothing in the sheet flags a mismatch (e.g. golden case: Ordinarie+Frequente+Poco sensibile
  requires w3 per Tab. 4.1.IV, which happens to match the golden `Z54="w3"`, but the sheet does
  not enforce this).
- **Decision**: added an extra informational `Check` ("Classe di apertura fessura conforme a Tab.
  4.1.IV") in `tool.run()`, comparing the user's `classe_apertura_fessura` against
  `strutture.shared.durability_cover.crack_width_limit(...)`, emitted in both `legacy_compat`
  modes (it does not change any numeric result, only adds visibility); skipped when the norm
  requires a decompression check instead of a crack-width limit (`crack_width_limit` returns
  `None`). Listed here rather than as a numeric fix because the sheet itself never performs this
  cross-check, so there is no cell behaviour to diverge from.
- **Clause**: NTC2018 Tab. 4.1.IV.

## 10. Additional — `Z12`/`Z14` never check NTC2018 §7.4.6.2.1 seismic longitudinal-reinforcement ratio limits (added 2026-09-21)

- The sheet checks the non-seismic §4.1.6.1.1 As,min/As,max (`Z12`/`Z14`) and the critical-zone
  stirrup detailing (§7.4.6), but never checks §7.4.6.2.1's seismic longitudinal ratio limits:
  `ρmin = 1.4/fyk` (tension zone), `ρmax = ρ'+3.5/fyk`, and the compression-steel ratio
  (`As' >= 0.5·As` for CD"A", `>= 0.25·As` for CD"B"). A section with e.g. B450C and
  `ρ = 0.0025 < 1.4/450 = 0.00311` would pass every sheet check while violating §7.4.6.2.1.
- **Decision**: added `armatura_limiti.duttilita_longitudinale_sismica` and three new `Check`s
  ("Percentuale di armatura tesa minima/massima sismica", "Armatura compressa minima sismica"),
  emitted in **both** `legacy_compat` modes (it's an additive check, not present in the sheet at
  all — same pattern as item 9's Tab. 4.1.IV conformity check). `n_ferri2`/`diametro_ferri2_mm`
  (already an input, used as extra tension steel elsewhere) is reused as the compression layer
  `As'` for this check only, to avoid adding a new input field.
- **Clause**: NTC2018 §7.4.6.2.1.
- **Numeric impact on the golden case**: new information only, not a `legacy_compat` divergence.
  The golden case (only ferri1, `n_ferri2=0`) fails both the new `ρmax` check (`ρ=0.00793 >
  ρmax=0.00700`, since `ρ'=0`) and the new `As'` check (`As'=0 < As',min=392.7mm²`), correctly
  surfacing that this section needs top reinforcement for CD"B" ductility that the sheet never
  flagged.

## 11. Additional — `Z32`/`Z33` stress-block factor 0.81 vs 0.8, and no ductility/compatibility check (corrected + added 2026-09-21)

- **Cell**: `Z32` = `As,o·fyd/(B·fcd)/0.81`.
- **Sheet behaviour**: uses `0.81` as the rectangular-stress-block reduction factor. NTC2018
  §4.1.2.3.4.2 fixes `λ=0.8` for `fck<=50MPa`. `MRd` (`Z33`) is accidentally unaffected (the
  factor is used both to compute `y` and to weight it back in the lever-arm term, so it cancels
  algebraically), but `y` — the only published quantity a user could use for a ductility
  screening — comes out ~1.25% below the true neutral-axis depth in legacy mode. The sheet also
  never verifies that the tension steel actually yields (`εs>=εyd`) before trusting `MRd`.
- **Fixed behaviour**: `flessione_slu.py` uses `λ=0.8` when `legacy_compat=False` (`λ=0.81`,
  matching the sheet, when `legacy_compat=True`); `MRd` is identical in both modes for this
  reason. A new `eps_s_permille`/`acciaio_snervato` compatibility check (Bernoulli, `εcu=3.5‰`,
  compared against `fyd/Es`) is added and emitted as a `Check` ("Duttilità sezione (acciaio
  snervato)") in **both** modes — additive, not a sheet divergence, since the sheet never
  performs this check at all.
- **Clause**: NTC2018 §4.1.2.3.4.2 (blocco di tensioni), §4.1.2.1.2.2 (εcu compatibility).
- **Numeric impact on the golden case**: `y` 66.395mm (legacy, `λ=0.81`) → 67.225mm (fixed,
  `λ=0.8`, ≈+1.25%); `MRd` unchanged (207.01 kNm) in both modes. The golden case is heavily
  under-reinforced, so the new ductility check passes (`εs≈13.9‰ >> εyd≈2.07‰`) in both modes.

## 6. Informational — `J58`/`J77` duplicate "classe di duttilità" input cells

- The sheet requires the same CD"A"/CD"B" choice to be typed independently into two disconnected
  cells (`J58` feeds `Lcr`/`K60`; `J77` feeds `K81`), with no formula tying them together — a
  user could set one without the other. `TraveRettangolareInput.classe_duttilita` collapses this
  into a single flat field feeding both computations, removing the desync risk. Not a numeric
  bug in the cached example (both cells hold `"CDB"`), so not counted as a `legacy_compat`
  divergence.
