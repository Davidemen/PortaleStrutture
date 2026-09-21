# Architecture — batch 2 (11 workbooks)

Extends `docs/architecture.md`; `docs/BUILD_CONTRACT.md` applies unchanged except §2 below (table inputs amend "inputs stay FLAT"). Specs: `docs/specs/<unit>.md`.

## 1. Module map

### 1.0 Package layout (decision)
`members` = resistance of ONE structural member from given design forces. Batch 2 adds two kinds of tool that are not that: soil response (no member at all) and foundations (reaction tables + soil + member design). Tools never import each other, so placement only drives UI grouping, ownership and disjoint directories for parallel agents:
- `strutture.geotechnics` — `cedimenti_edometrico`, `cedimenti_elastico`. UI group `Geotecnica / Cedimenti`.
- `strutture.foundations` — `plinti_isolati`, `plinti_pali`, `travi_collegamento`, `pavimento_industriale`. UI group `Fondazioni / …`.
- `strutture.members` — new `ca_punzonamento`, `acciaio_sezione_composta`; extended `ca_pilastri`, `ca_taglio_non_armato`, `acciaio_incendio`.
- `muro` stays in `members` (no move: would break batch-1 paths while it is still being finished).
- Required orchestrator edit (protected file): `shared/tool.py` `TOOL_PACKAGES += ("strutture.geotechnics", "strutture.foundations")`. Tests mirror: `tests/geotechnics/<pkg>/`, `tests/foundations/<pkg>/`.

### 1.1 Tool packages (ONE composed tool per sheet-level workflow; analyst "tools" become step modules)
| Package | Tool(s) (`name`) | Result groups (nested frozen models) | Spec § | Reuses (existing shared) |
|---|---|---|---|---|
| `geotechnics/cedimenti_edometrico` | `geo-cedimento-edometrico` | `carico` (q', σ'v0), `profondita_critica` (z_crit Cardano + criterio 0.1σ'v), `righe` (z, Δσ approx, Δσ Newmark, Eed, ΔH, ΣΔH; `chart`), `cedimento` (w_ed highlight) | edometrico | `numeric`, `tables`, `units` |
| `geotechnics/cedimenti_elastico` | `geo-cedimento-elastico-newmark` (`modalita: CENTRO\|PUNTO`), `geo-cedimento-elastico-timoshenko-goodier` | newmark: `carico`, `righe` (z, Iz per sub-rectangle, Δσ, E, Δw; chart), `cedimento` (w_O, w_O' o QA Boussinesq); T-G: `geometria` (B', m, n), `modulo` (Es pesato), `fattori` (IS centro/bordo, IF), `cedimento` | elastico (both) | `numeric`, `tables`, `units` |
| `foundations/plinti_isolati` | `fond-plinto-isolato` (steps = analyst tools 1+2 composed) | `materiali`, `righe` (per combo: N, M, e, σt, μ_rib X/Y, μ_scorr, compresso), `inviluppo` (per family × quantity: valore + combo governante), `eccentricita`, `flessione` (MEd, As, n, Ø, callout), `sle` (σc, σs QP/CAR/FREQ) | plinti-isolati | `materials`, `rebar_catalog`, `ntc_combos`, `durability_cover`, `section_geometry.cracked` |
| `foundations/plinti_pali` | `fond-plinto-su-pali` (4 analyst tools → 4 step groups) | `righe` (per LCC: N per fila/palo, M), `inviluppo` (Nmin/Nmax/M±/V + combo), `flessione` (inf/sup X/Y), `puntone` (θ, Fus, σRd,max, ws), `tiranti` (XY, X, Y), `taglio`, `punzonamento`, `pali_in_trazione` (only when Nmin<0) | plinti-pali | `materials`, `rebar_catalog` |
| `foundations/travi_collegamento` | `fond-trave-collegamento` (`norma: NTC2018\|EN1998`) | `sismica` (S, a_max, α), `azione` (NEd), `materiali`, `compressione`, `trazione`, `snellezza`, `minimi` (geom., ρ_l, staffe) | travi-coll. (both sheets) | `ntc_site_seismic.amplificazione` (replaces `Tabelle!N119:N121` cross-sheet refs), `materials`, `rebar_catalog`, `section_geometry` |
| `foundations/pavimento_industriale` | `pavimento-industriale` (materiali+distribuiti+concentrati+giunti = one sheet), `pavimento-eisenmann-coefficiente` (unwired table, useful alone) | `materiali`, `sottofondo` (k, D, l), `distribuiti`, `concentrati` (tuple: caso × posizione), `punzonamento`, `giunti` | pavimento (all) | `materials.concrete`, `rebar_catalog`, `tables.interp_lookup` |
| `members/ca_punzonamento` | `ca-punzonamento` | `geometria` (u0, d), `faccia_pilastro` (vEd0 vs vRd,max), `perimetro_critico` (scan rows + governing a/d; chart), `armatura` (only if check fails: Asw, fywd,ef, u_out, n. cuciture) | punzonamento | `numeric`, `units` |
| `members/acciaio_sezione_composta` | `acciaio-sezione-h-rimpiattata` | `elementi` (per piatto: A, x, y, Δ, Wpl,i, I,i), `sezione` (A, xN, yN, Wpl,x, Wpl,y, Iy, Iy,base); rows 16–50 not ported | small-units §3 | `materials.structural_steel` |
| `members/ca_pilastri` (ext.) | unchanged names `ca-pilastro-rettangolare/-circolare` + `norma` | unchanged + `regole` (rule set echo) | pilastri-ntc2018, -ec2 | as today |
| `members/ca_taglio_non_armato` (ext.) | unchanged `ca-taglio-non-armato` | unchanged | small-units §2 | as today |
| `members/acciaio_incendio` (ext.) | new `acciaio-proprieta-temperatura` | `fattori` (ky, kp, kE), `proprieta` (fp,θ fy,θ Ea,θ) | small-units §1 | `fire_reduction.reduction_factors` |

Tool-local (single consumer → `tables.py`, promote on second consumer): Winkler k table, Materiali pavimento, EN 1998 soil S/α (`M131:P134`), NTC §7.2.5 α table, Eisenmann 160 rows.

### 1.2 New shared modules (`src/strutture/shared/<name>/`, pure, frozen results, SI-engineering units)
| Module | API | Consumers |
|---|---|---|
| `soil_stress` | `newmark_corner(q_kPa, a_m, b_m, z_m) -> float` (atan branch fix when m²n²>m²+n²+1); `under_center(q,B,L,z)`; `under_point(q,B,L,x_m,y_m,z) -> PointStress{total, parts: tuple[4]}` (signed 4-rectangle superposition, point may be outside); `spread_2to1(q,B,L,z)`; `ic_center(B,L,z)`; `steinbrenner_is(m, n, mu) -> float` | both cedimenti pkgs |
| `soil_layers` | `SoilLayer{z_top_m, z_bot_m, modulo_MPa}` (frozen row model, reused as INPUT row); `validate(layers)` (ascending, contiguous, no overlap); `layer_at(layers, z) -> SoilLayer` raises `KeyNotFound` past coverage (`legacy=True` → `None` = zero contribution); `depth_grid(z_max, dz) -> tuple[float,...]`; `weighted_modulus(layers, h)` (any n, not 4) | both cedimenti pkgs |
| `footing_pressure` | `uniaxial(n_kN, m_kNm, b_m, l_m) -> {e, in_kern, sigma_max, sigma_min, contact_len}`; `biaxial(n, mx, my, bx, by) -> {sigma_corners[4], sigma_max, compressed_ratio, in_kern}` (Navier inside kern; partial contact via `numeric.bisect`, see §8-D2) | plinti_isolati; later muro (not refactored now) |
| `load_table` | `ReactionRow{nodo, combo, famiglia, fx_kN, fy_kN, fz_kN, mx_kNm, my_kNm, mz_kNm}`; `Famiglia = Literal["SLU_STR","SLU_EQU","SLV_STR","SLV_EQU","SLE_RARA","SLE_FREQ","SLE_QP"]`; `envelope(rows, value: Callable, mode: max\|min\|absmax, by: famiglia\|None) -> tuple[EnvelopeRow{famiglia, valore, combo, nodo, indice}]`; `governing(rows, value, mode)`; ties → first row (= XLOOKUP) | plinti_isolati, plinti_pali |
| `pile_group` | `PilePos{x_m, y_m}`; `pattern(n, sx, sy) -> tuple[PilePos]`; `rigid_cap_axial(n_kN, mx, my, piles) -> tuple[float]` (N/n ± M·x/Σx²) | plinti_pali |
| `ec2_shear` | `k_size(d_mm)` (≤2.0), `v_min`, `v_rd_c(k, rho, fck, sigma_cp, gamma_c, *, av_over_2d=None)`, `control_perimeter(shape: rett\|circ, a, b, dist) -> {u_mm, area_mm2}`, `v_rd_max(fck, gamma_c)`, `fywd_ef(d_mm, fywd)` (capped, eq. 6.52), `scan_governing(f, lo, hi, step)` | punzonamento, plinti_pali, pavimento. `ca_taglio_non_armato` keeps its own copies until batch 1 is frozen, then becomes thin re-exports |
| `ec2_strut_tie` | `sigma_rd_max(fck, nodo: CCC\|CCT\|CTT, gamma_c)`, `strut_capacity(...)`, `tie_area(f_kN, fyd)` | plinti_pali (`ca_mensole` untouched) |
| `tabular` | `RowModel` base (frozen, scalar-only fields), `table_field(row_model, *, max_rows, key, aliases…)` building the `Field` + hints of §2, `row_errors(exc) -> tuple[(row, col, msg)]` | every table tool |
| `units` (edit, allowed) | add `kgcm2_to_kPa` (98.0665), `cm_to_m`, `kgm3`→`kN/m³` | geo tools |

## 2. Table inputs (new contract)
**Shape.** A table is one input field `tuple[Row, ...] = Field(min_length=1, max_length=N, json_schema_extra={"widget": "table", "table": {...}})` where `Row(RowModel)` is frozen, flat, scalar-only; every column keeps the normal field contract (Italian `description`, `unit`, `symbol`, bounds, `Literal` enums). Contract amendment: inputs = flat scalars + table fields; no other nesting. Cross-row rules (contiguous layers, unique `combo` per `nodo`) live in a `model_validator(mode="after")` raising Italian `ValueError`s naming the 1-based row.

| Table | Row columns (unit) | max rows | Notes |
|---|---|---|---|
| `strati` (cedimenti ×3) | `z_top_m`, `z_bot_m` (m from ground), `modulo_MPa` (Eed or E) | 20 | sheet hard-codes 5/4; base-relative depths derived |
| `reazioni` (plinti isolati/pali) | `nodo` (int), `combo` (str ≤64), `famiglia` (enum), `fx_kN fy_kN fz_kN mx_kNm my_kNm mz_kNm` | 20 000 | `famiglia` column replaces the sheet's hard-coded row ranges `INPUT!AE4:AG10`; pali: `famiglia` optional (`None` → one global envelope). One footing TYPE per run; rows of many nodes allowed, envelope reports `nodo` |
| `carichi` (pavimento) | `caso`, `posizione` (centro\|bordo\|spigolo), `p_kN`, `impronta_a_mm`, `impronta_b_mm`, `gamma`, `psi1` | 12 | replaces 2×3 column blocks; fixes `$L$6` absolute-ref bug by construction |
| `piatti` (H rimpiattata) | `b_mm`, `h_mm` | 10 | legacy = 5 fixed rows, `b=0` disables |
| pile layout | none: `schema_pali` enum + spacing scalars as in sheet (§8-D5) | — | shared helper already takes coordinates |
Generated grids (z every 10 cm, a/d 0.5…2.0) are NOT inputs: scalars `dz_m`, `z_max_m`, `passo_scan` with sheet defaults; they come back as output rows.

**Hint contract (extends DESIGN_SPEC §4; all optional, UI never branches on tool name).** JSON schema emitted by pydantic: `{"type":"array","items":{"$ref":"#/$defs/Row"},"minItems","maxItems"}`; columns = `items.properties` in declaration order, headers = `symbol`+`description`+`[unit]` exactly like output row tables.
| Key | Where | Type | UI effect | Absent → |
|---|---|---|---|---|
| `widget: "table"` | in array field | str | row editor (add/duplicate/delete/move, Tab/Enter grid navigation) | any array-of-objects still renders the same editor |
| `table.paste` | in array field | bool (default true) | `Incolla da Excel` textarea/clipboard: TSV or `;`-CSV, decimal comma or point, thousands separators rejected, blank lines skipped; replaces or appends | — |
| `table.csv` | idem | bool | `Carica CSV` (`FileReader`, UTF-8/BOM, same parser) + `Scarica modello CSV` (header row only) | hidden |
| `table.key` | idem | column name | row label in errors/envelope (`combo`) | 1-based index |
| `table.fixed_rows` | idem | bool | no add/delete (legacy 5-plate table) | free rows |
| `table.preview_rows` | idem | int (default 50) | above it the editor collapses to `N righe caricate` + first/last preview; still editable via paste/CSV | 50 |
| `aliases` | row column | `list[str]` | header auto-mapping on paste (`"Fz"`, `"FZ (kN)"`, `"Load"`, MIDAS names); header row detected when a numeric column holds non-numeric text; no header → positional | positional only |
Validation errors: API must expose pydantic `loc` (`["reazioni", 17, "fz_kN"]`) so the widget marks the cell (web-layer change: `shared/tool.execute` message + `loc` list; orchestrator task). Body limit: `STRUTTURE_WEB_MAX_BODY_BYTES` default 1 MB → 8 MB (10 634 rows ≈ 1.6 MB JSON). Tables > `preview_rows` are not persisted to `localStorage`. `Tool.example` carries ≤ 30 representative rows; full golden table lives in test fixtures.

**Result of a many-rows tool** (uniform across tools): `righe: tuple[RowResult,...]` (all rows, same order, key columns echoed; rendered by existing row table + CSV; output hint `rows_page: 200`), `inviluppo: tuple[EnvelopeRow,...]` (quantity × famiglia → value, governing `combo`/`nodo`/row index), `governante: RowResult` groups fully expanded for the ≤3 highlight quantities. `checks` are emitted on the envelope only (one per verification × famiglia, `detail` = governing combo, `value/limit/unit` filled) — never one check per row. Undefined ratios (zero demand) are `None` + flag `senza_domanda`, never the string `">100"`. Print relazione: echo tables > 50 rows as first/last 5 + count + SHA-256 of the canonical TSV.

## 3. Columns: NTC 2008 / NTC 2018 / EN 1992-1-1 in `members/ca_pilastri`
ONE design: add `norma: Literal["NTC2018","EC2","NTC2008"] = "NTC2018"` to both input models; keep the two tool names (deep links, fixtures). ~9 cells differ per sheet, so no new tools and no copy of the package.
- New `regole.py`: frozen `RuleSet{lambda_lim_formula, ned_factor, l0_mode, raggio_inerzia: netto|lordo, nu1, ac_condition, as_min_combinator, rs_controlla_minimo, staffe_candidati, diametro_min_barre, A, B, C}` and `RULES: Mapping[tuple[Norma, bool], RuleSet]`. `tool_*.py` resolves `RULES[(norma, legacy_compat)]` once and passes explicit keyword parameters to steps. Step functions keep their current signatures; new rule parameters are keyword-only with defaults equal to today's behaviour, so existing step unit tests stay untouched.
- `legacy_compat=True` = that norm's OWN sheet as oracle: NTC2008 → existing fixtures (unchanged JSON); NTC2018 → `ca-pilastri-ntc2018`; EC2 → `ca-pilastri-ec2` (cells shifted +1 row: per-norm cell maps in the gen scripts). New fixtures `ca_pilastri_<forma>_{ntc2018,ec2}_oracle.json`.
- `legacy_compat=False` = the norm's own text: NTC2018 + Circ. 2019, or EN 1992-1-1 with Italian NA (α_cc=0.85 stays, §8-D3).
- Current "code-standard" branch (2008 sheet with bugs fixed, already targeting NTC 2018) BECOMES `(NTC2018, False)`. It is reconciled against the 2018 sheet: where the sheet now agrees (×1000 in λlim, l0=β·H) nothing changes; where it differs (gross vs net `i`, dropped ρ_min in rs check, `Ned=0` ac-selector, MIN vs MAX As,min, single-hinge capacity shear) the norm text wins and the sheet value goes to `docs/divergences/ca-pilastri.md`. Existing fixed-behaviour tests (no `norma`) therefore keep their meaning.
- `(NTC2008, False)` is rejected by a model validator ("NTC 2008: disponibile solo come riproduzione del foglio") — a superseded norm gets no maintained code-standard branch.
- Only mechanical edit to batch-1 tests: golden/oracle helpers add `norma="NTC2008"`; expected numbers and JSON untouched. EC2-only inputs (`phi_ef`, `rm`) use `condition: {"field":"norma","equals":["EC2"]}`. Circular golden: slenderness verdict flips OK→NO between 2008 and 2018 — assert both explicitly.
- Same pattern, smaller: `fond-trave-collegamento` has `norma: NTC2018|EN1998` with one oracle fixture per sheet.

## 4. Taglio non armato v2 · fuoco-materiali
- **Taglio v2 → same tool, optional inputs.** `fck_MPa: float | None = None` (None → 0.83·Rck as v1), `gamma_c: float = 1.5`, `asl_mm2: float | None`, `n_barre`/`diametro_barre_mm` (validator: exactly one way to give Asl). Warning when both Rck and fck are given and |fck − 0.83·Rck| > 5 %. σcp stays NEd/(bw·h) (not a bug). Second oracle fixture `ca_taglio_non_armato_v2_oracle.json` (slug `ca-taglio-non-armato-v2`, sheet `1m`); v1 fixture untouched. No new tool, no new divergence.
- **Fuoco-materiali → new tool in `members/acciaio_incendio`** (`temperatura.py`, `tool_temperatura.py`): inputs `theta_C` (20–1200), `fyk_MPa`, `ea_MPa`; calls `shared.fire_reduction.reduction_factors` (already returns ky, kp, kE). The existing `acciaio-resistenza-incendio` (time → ISO 834 → θ) is untouched; the two tools share only the shared module. The per-sheet `FORECAST.LINEAR` bracket is a manual-edit hazard, not a formula to reproduce: both modes interpolate the full Table 3.1; `legacy_compat` has no numeric divergence when the bracket was right (all four sheets). 550/600/650/700 °C sheets = 4 free golden cases.

## 5. Build order
- **B0 — enablers (serial, orchestrator-owned files; S unless noted).** `TOOL_PACKAGES`; `units` additions; validation `loc` in error envelope + body limit; `extract.fixtures.generate` extension: overrides/reads on several sheets (`"CHECKS!AA6"` addresses) — needed by plinti; `shared/tabular` S; UI table widget + paste/CSV parser + e2e **L** (dir `web/static*`, parallel to everything).
- **B1 — shared + leaves with no new shared deps (parallel, disjoint dirs).** `soil_stress` M · `soil_layers` S · `footing_pressure` M · `load_table` M · `pile_group` S · `ec2_shear` M · `ec2_strut_tie` S ‖ `acciaio-proprieta-temperatura` S · taglio v2 S · `acciaio_sezione_composta` M · `travi_collegamento` M.
- **B2 — tools (parallel).** `cedimenti_edometrico` M · `cedimenti_elastico` **L** · `ca_punzonamento` **L** · `pavimento_industriale` **L** · `plinti_isolati` **L** · `ca_pilastri` norma refactor **L** (rett → circ sequential, single owner).
- **B3 — pile caps + integration.** `plinti_pali` **XL** (inviluppo → flessione → puntone/tiranti → taglio/punzonamento, sequential inside one agent) · hints/`check_hints.py` run, divergence docs, Windows check, perf test M.
- Batch-1 dependencies: `ca_pilastri` and `ca_taglio_non_armato` must be green and FROZEN before their B1/B2 extensions start (same directories, one owner at a time). `muro` keeps its private base-pressure step; migrating it to `footing_pressure` and `ca_mensole` to `ec2_strut_tie` is deferred tech debt, not batch 2. `section_geometry.cracked` and `rebar_catalog` APIs are consumed read-only.
- Totals ≈ 1 XL, 6 L, 9 M, 8 S. Critical path: B0 (`generate` multi-sheet + table widget) → `load_table` → `plinti_isolati` → `plinti_pali`.

## 6. Test strategy deltas
- **Golden rows.** Table inputs are stored once as `tests/fixtures/<tool>_golden_rows.csv` (UTF-8, `newline=""`, extracted from `build/data/...` by a committed gen script), loaded by a test helper into row models. Assertions: every envelope/design cell at `rel=1e-6` + a row sample (first, last, each family's governing row, one row per branch: e inside/outside kern, N<0, zero shear). Depth/scan grids: rows at z=0, each layer boundary, cutoff row, last row, plus the sum.
- **Oracle for table tools.** A case = a handful of cell overrides in 2–3 rows (first, middle, last of a family) + scalar overrides; read those rows' computed cells + all envelope cells. The Python side applies the same overrides to the golden rows (`apply_overrides(rows, case)` helper in `tests/support`). 6 cases max for the 10 k-row pile workbook (LibreOffice recalc is slow); 8–10 elsewhere. XLOOKUP governing-combo cells are already normalised by `extract.oracle`; compare names as strings, ties resolved first-match.
- **Invariants (unit).** Envelope = max over per-row results; invariant under row permutation except tie order; one-row table ≡ scalar calculation; 10 634 rows run < 2 s; `max_length`+1 rows → validation error; paste parser cases (decimal comma, header aliases, trailing tabs) in the web test suite.
- **Free golden cases.** geo-cedimenti `350`, `400`, `500` (PUNTO mode; all have F7=F8=F9=F10 so add one hand-computed asymmetric case against `soil_stress.under_point`), `elastico-centrale-newmark` (CENTRO), punzonamento `shotblast-375n`, fuoco 550/600/650/700. T-G v1/v2 sheets are dead drafts — excluded.
- **Columns.** 3 norms × 2 shapes fixtures; batch-1 fixtures must pass byte-unchanged (CI guard: fixture JSON hash).

## 7. Suspected spreadsheet bugs — `legacy_compat=True` reproduces, `False` fixes (F) or keeps + "Da verificare" (V)
| Unit · cell | Sheet behaviour | Code-standard |
|---|---|---|
| edometrico B18/B24:B28 | z_crit hard-coded 10000; Cardano root never assembled | F: z_crit = u+v−(B+L)/3 computed; input override optional |
| edometrico J, newmark S, 500 L | layer lookup → 0 past coverage, div/0 or IFERROR→0 settlement | F: `CalcError` "stratigrafia non copre z" |
| edometrico B8 | unlabeled embedment, unit inferred | V: labelled `D` [m], flagged |
| edometrico M | reset-to-0 + MAX idiom | same result, implemented as cumulative sum to cutoff (no divergence) |
| newmark T6 vs Z6 | sums to row 1063 vs row 87 | F: both to same z_max |
| newmark F | E literal inside formula | input column (no numeric divergence) |
| 500 M/N, AK/AL | sub-rectangles `Ofga`/`Ocde` pair two segments of the same side | F: `under_point` by coordinates; V until an asymmetric hand case confirms |
| T-G-3 N17/P17 | (1−μ) | F: (1−μ²) per workbook's own reference figure; ≈ +35 % at μ=0.35 |
| T-G-3 H11 | Es average hard-wired to 4 layers | F: any n within H |
| plinti-isolati CHECKS!AA | σt = two uniaxial maxima − N/A | F: `footing_pressure.biaxial` (§8-D2) |
| plinti-isolati AM, P16… | zero shear → text `">100"` | F: `None` + `senza_domanda` |
| plinti-isolati T13/T14 | ULS moment uses SLS-QP family pressure | F: ULS families only (§8-D4) |
| plinti-isolati AE4:AG10, rows 543+ | hard-coded family row ranges; dead rows | F: `famiglia` column; dead rows not ported |
| plinti-isolati O11/S11 | symbol `s` reused | renamed fields, no numeric change |
| plinti-pali AF12 | self-weight /1.4·0.9 vs γG1=1.3 | F: /γG1·0.9 |
| plinti-pali AR79/AR80 | Msd literals 775/710.5 ≠ envelope 862.4/790.6 | F: wired to envelope; legacy = explicit override inputs |
| plinti-pali AR97 | av=470 vs doc "Ø/5" | V: av stays input, warning when ≠ derived |
| plinti-pali AR99 | k not clamped ≤ 2 | F |
| plinti-pali AR110 | punching u at column face | V (kept, labelled §6.4.5 u0 check) |
| plinti-pali AR93 | 0.26 fctm/fyk computed, unused | F: enters As,min |
| plinti-pali AV51/AZ51 | 3.14 | F: π |
| plinti-pali VLOOKUP mm/25.4 | exact match on float → IFERROR→0; inch inputs BL19/29/40 | F: `rebar_catalog` in mm; legacy accepts mm and converts |
| plinti-pali BP:BX | tension-pile block always computed, never reported | F: gated on Nmin<0 and reported |
| punzonamento D55 | list has 28 for 18 | F: 18; legacy accepts 28 |
| punzonamento E14, E55 | dead formula; unit label | not ported |
| punzonamento H56 | fywd,ef uncapped | F: `min(…, fywd)` |
| punzonamento D41:D62 | reinforcement block ungated, negative values | F: group `None` when not required |
| pavimento G22 | sup check /fcfk, inf /fcfd | F: fcfd both |
| pavimento M33/N33 | u1 with h instead of d | F: d |
| pavimento I39 | label 1.2, formula 1.5 | V: 1.5 kept, flagged |
| pavimento `$L$6` | centro factor for all positions | F by row table |
| travi-coll. check_lambda | label direction swapped | formula kept, label fixed |
| travi-coll. P118 vs P131 | α_A 0.2 (NTC) vs 0 (EN) | intentional per norm; V on NTC value |
| pilastri 2018 CX38, H24/J24, J56/J63, MIN As | see §3 | norm text wins; rows in divergences |
| pilastri EC2 A=C=0.7, α_cc | hard-coded | F: C=1.7−rm, A from φ_ef when given; α_cc V |
| H rimpiattata H6 | last yN term uses x | F |

## 8. Open decisions (recommendation first)
- **D1 Units of geotechnical tools.** Recommend SI-engineering inputs (m, kPa, MPa; settlement out in mm and cm) with `units` conversions and oracle helpers converting to the sheets' cm–kg/cm²; alternative = keep sheet units.
- **D2 Biaxial base pressure outside the kern.** Recommend exact Navier inside the kern + numerical partial-contact solver (plane pressure, no tension, `bisect`) in `footing_pressure` (M effort); fallback = sheet superposition in both modes with a warning.
- **D3 Columns.** Recommend default `norma="NTC2018"`, NTC 2008 only as sheet reproduction, and `EC2` = EN 1992-1-1 with the Italian National Annex (α_cc=0.85), stated in `Tool.norm`.
- **D4 Isolated-footing engineering intent.** Recommend ULS-only families for MEd (drop SLS-QP) and live envelope moments in pile caps instead of the 775/710.5 literals; needs the engineer's confirmation that these were not deliberate.
- **D5 Pile layout + table size.** Recommend sheet-style `schema_pali` enum + spacings now (strut-and-tie geometry is pattern-specific) with a general coordinate helper underneath; free pile-coordinate table later. Cap `reazioni` at 20 000 rows and return all per-row results (paged UI, CSV export).

## 9. Decisions taken by the user (2026-09-21) — these override the recommendations above where they differ
- **D1 Units: BOTH.** Geotechnical tools take `sistema_unita: Literal["SI", "tecnico"] = "SI"` ("SI" = m, kPa, MPa; "tecnico" = the sheets' cm, kg/cm²). Dimensional input fields carry unit-neutral names (`z_top`, `modulo`, `q`) plus the hint `unit_options: {"SI": "m", "tecnico": "cm"}` instead of a single `unit`; the model has `json_schema_extra={"unit_selector": "sistema_unita"}` at model level. Conversion to SI happens once at the boundary (`shared/units`), all step modules compute in SI; results are always reported in SI with settlements in both mm and cm. Oracle/golden tests feed the sheet's own numbers with `sistema_unita="tecnico"`. The web form relabels units when the selector changes (values are NOT converted) — DESIGN_SPEC §4b.
- **D2 Base pressure outside the kern: BOTH.** `metodo_pressioni: Literal["esatto", "sovrapposizione"] = "esatto"` on the footing tools: "esatto" = Navier inside the kern + no-tension plane solver outside (bisect), "sovrapposizione" = the sheet's method, available in normal mode with a warning when the resultant is outside the kern in both directions. `legacy_compat=True` forces "sovrapposizione".
- **D3 accepted.** Columns default `norma="NTC2018"`; NTC 2008 only as sheet reproduction; EC2 = EN 1992-1-1 with the Italian National Annex, stated in `Tool.norm`.
- **D4 NOT deliberate -> fix.** Isolated footings: MEd from ULS families only (SLS-QP excluded). Pile caps: live envelope moments instead of the literals 775 / 710.5. `legacy_compat=True` reproduces the sheet; both go in the divergence docs with their numeric impact on the golden case.
- **D5 accepted.** `schema_pali` enum + spacings now, general coordinate helper underneath; `reazioni` capped at 20 000 rows, all per-row results returned (paged UI, CSV).
