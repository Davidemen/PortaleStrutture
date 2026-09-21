# Divergences — shared CA packages (`rebar_catalog`, `durability_cover`, `section_geometry`)

These three packages are pure data/formula libraries (no `Tool` registration), so there is no
`legacy_compat` on a Tool input model here; instead each function takes its own
`legacy_compat: bool = False` flag where the sheet's lookup behaviour is fragile.

## Crack-control table lookup (`rebar_catalog.crack_tables`)

- **Cell**: `Tabelle!N67:R93` (Ø-vs-σs table, Tab. C4.1.II), referenced by `ca-travi.md` Tool 5
  step `σs,limite [AI54]`.
- **Sheet behaviour**: `VLOOKUP(Ømax, ..., FALSE)` — exact match only. Any bar diameter not
  present as a literal row (e.g. 15mm, 34mm) raises `#N/A` in Excel; the sheet's dropdown for
  Ø only offers the tabulated diameters, so the bug never surfaces in practice, but a caller
  passing an arbitrary diameter would hit it.
- **Fixed behaviour**: `legacy_compat=False` linearly interpolates sigma_s between the two
  bracketing table diameters (`shared.tables.interp_lookup`), giving a continuous, physically
  reasonable limit for any diameter in range instead of an error.
- **Clause**: NTC2018 Tab. C4.1.II.
- **Numeric impact**: none on the `ca-travi` golden case (Ø=20mm is an exact table row in both
  modes: σs,limite = 240 MPa either way). The divergence only bites for off-row diameters.

## Sigma_s-vs-spacing table (`rebar_catalog.crack_tables.sigma_limit_by_spacing`) — fixed (was inverted)

- No cell in `ca-travi`/`ca-mensole`/`ca-pilastri` `Tabelle` (the only sources listed for this
  task) tabulates sigma_s against bar spacing; only the Ø-vs-σs table (Tab. C4.1.II) is present.
- **Bug (previous behaviour)**: `_SPACING_LIMITS` was keyed `sigma_s [MPa] -> max spacing [mm]`
  (the norm's native direction) but `sigma_limit_by_spacing(spacing_mm)` looked the *spacing* up
  in that same first column, i.e. treated it as `spacing -> sigma_s`. This silently returned
  wrong values for every call (e.g. `sigma_limit_by_spacing(200.0)` returned 250.0 instead of
  240 MPa) and raised `KeyNotFound` for well-behaved small spacings. It also only ever held one
  crack-width column (no `w_class` parameter), so w1 (0.2mm) callers would have silently reused
  the loosest (then-mislabelled) column.
- **Fixed behaviour**: the table is now genuinely keyed `spacing_mm -> sigma_s_MPa`, one column
  per `CrackWidthClass` (mirroring `sigma_limit_by_diameter`'s `w_class` parameter), inverted
  from EN1992-1-1 Table 7.3N / NTC2018 Tab. C4.1.III (per-σs max-spacing) into the
  per-spacing max-σs direction actually needed at the call site (given an as-built spacing,
  what steel stress does it satisfy). `w2` (wk=0.3mm) pairs — (50,360),(100,320),(150,280),
  (200,240),(250,200),(300,160) — are the ones explicitly checked against the published norm
  text; `w1` (wk=0.2mm) and `w3` (wk=0.4mm) are the same published table's other two columns,
  inverted the same way.
- **Clause**: NTC2018 Tab. C4.1.III / EN1992-1-1 Table 7.3N.
- **Numeric impact**: no golden/oracle case in this package calls `sigma_limit_by_spacing`
  (only unit tests exercise it directly), so no golden numbers change. `sigma_limit_by_spacing`
  is now a 2-positional-argument function (`spacing_mm, w_class`); any future caller must pass
  the crack-width class.
- This settles the previous "Da verificare" entry — the six wk=0.3 pairs are confirmed against
  the published EC2/NTC2018 table text; the w1/w3 columns are the same table's other two
  columns and share that confidence level (not independently re-derived from a sheet cell).

## Crack-width limit table blank cells (`durability_cover.crack_limits`)

- **Cell**: `Tabelle!M56:Q62` (Tab. 4.1.IV). Three combinations are blank in the sheet:
  (`aggressive`, `quasi permanente`, `sensibile`), (`molto aggressive`, `frequente`,
  `sensibile`), (`molto aggressive`, `quasi permanente`, `sensibile`).
- **Sheet behaviour**: the cell is simply empty; a formula reading it would get `0`/blank
  silently.
- **Fixed behaviour**: `crack_width_limit(...)` returns `None` for these three combinations
  instead of a spurious width class, so callers must handle the "not applicable" case
  explicitly (NTC2018 requires a decompression check there, not a crack-width limit).
- **Clause**: NTC2018 Tab. 4.1.IV. No numeric impact on any golden case (all three golden
  scenarios in `ca-travi`/`ca-mensole`/`ca-pilastri` use "Ordinarie"/"Poco sensibile").

## Cracked-section formula generalisation (`section_geometry.cracked_neutral_axis`)

- The sheet (`ca-travi.md` Tool 4, `y [Z38]`) only ever computes the singly-reinforced case
  (`As2=0`). `cracked_neutral_axis` generalises to a doubly-reinforced rectangular section
  (compression steel `As2` at depth `d2`) using the standard homogenised first-moment-of-area
  equation; with `as2_mm2=0` it reduces exactly to the sheet's closed-form root (verified by
  the golden test against B=600mm, d=330mm, As=5·Ø20 → x=126.44mm, matching the spec's
  `y[Z38]=126.44mm` to 4 significant figures). Not a bug fix — an intentional widening of the
  shared module's scope beyond what any single sheet needs, so other CA tools with compression
  reinforcement can reuse it without reimplementing the algebra.
