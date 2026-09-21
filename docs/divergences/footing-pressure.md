# Divergences — `strutture.shared.footing_pressure`

Source: `docs/specs/fond-plinti-isolati.md` Tool 1 (`CHECKS` sheet), §7/§8-D2/§9-D2 of
`docs/architecture-batch2.md`. This module has no `legacy_compat` flag of its own (it is shared
physics, not a Tool); the fix below is exposed as a second `metodo`, selectable by the calling
Tool (`plinti_isolati`, per the module map) which owns `legacy_compat`.

## CHECKS!AA — biaxial pressure superposition is an approximation

**Sheet behaviour**: `σt = MAX(σx range) + MAX(σy range) − N/(AX·BY)` — the two independent
uniaxial trapezoid maxima added and de-duplicated of one baseline term. Not the exact biaxial
corner/no-tension pressure (spec §7: "not the exact biaxial-bending corner pressure... verify
against a manual biaxial check").

**Fixed behaviour**: `footing_pressure.pressure(..., metodo="esatto")` (the default) computes the
exact linear Navier plane inside the biaxial kern and solves the no-tension plane-pressure problem
(2-D Newton fixed-point on the clipped rectangle, `no_tension.py`) outside it — see
`docs/architecture-batch2.md` §8-D2 / §9-D2. `metodo="sovrapposizione"` reproduces the sheet's
formula exactly (`sovrapposizione.py`); a Tool with `legacy_compat=True` must force this metodo.

**Clause**: NTC2018 §6.4.2.1 (rigid-footing contact pressure).

**Numeric impact on the golden case** (ULS1, node 1832: N=2596.93 kN, MYY=1.42918 kNm,
MXX=40.9685 kNm, AX=BY=4000 mm — ex=0.00055 m, ey=0.015776 m): both eccentricities are tiny and
deep inside the biaxial diamond kern (|ex|/(AX/6) + |ey|/(BY/6) ≈ 0.025), where the exact Navier
plane and the sheet's superposition coincide almost exactly. `sovrapposizione` reproduces the
sheet's σt=1.66283 kg/cm² exactly (see `test_sovrapposizione.py`); `esatto` gives
σmax=166.283 kPa ≡ 1.66283 kg/cm² under the same /100 sheet-style conversion (see note below) —
no measurable numeric impact on this particular golden case (agreement to 6 significant figures).
The two methods only diverge meaningfully once the resultant approaches or leaves the kern in one
or both directions (e.g. any case with both directions outside their own 1-D kern —
`sovrapposizione` then emits a `warning`, see below — or the biaxial-outside-kern property cases in
`tests/shared/footing_pressure/test_no_tension.py`, where only `esatto` is exact).

`sovrapposizione`'s `sigma_min_kpa`/`corners_kpa`/`compressed_ratio` fields are this module's own,
documented extension of the sheet's method (the sheet only ever computes the combined *maximum*,
`AA`; there is no sheet cell for a combined minimum) — not a divergence, since nothing in the sheet
is being reproduced incorrectly; flagged here for transparency. A `warning` is set on the result
whenever both ex and ey individually fall outside their own 1-D kern (§9-D2's "warning when the
resultant is outside the kern in both directions").

## Da verificare — sheet's kg/cm² columns use an approximate MPa→kgf/cm² factor

`docs/specs/fond-plinti-isolati.md` "Constants": `CHECKS!O..R` etc. multiply MPa by the literal
`10` (not the exact 98.0665 kPa per kgf/cm², i.e. `1 kgf/cm² ≈ 10.1972` in reality, not `10`). This
module computes exclusively in exact SI kPa (`shared.units` is not used here at all — no unit
selector applies to this physics-only module). **Consequence for the plinti_isolati Tool
(consumer, another agent/wave)**: when reproducing the sheet's cached kg/cm² golden/oracle values
in `legacy_compat=True`, converting this module's kPa outputs with the exact
`shared.units.kpa_to_kgcm2` (÷98.0665) will NOT match the sheet's own numbers — divide by 100
instead (equivalently, multiply the sheet's kg/cm² cached values by 100 to compare against this
module's kPa). Verified against the golden case: `162.442 kPa / 100 = 1.62442` matches
`CHECKS!R6=1.62442` cached in the spec to 6 significant figures; `/98.0665` gives `1.6565`, a ~2%
mismatch. Kept "Da verificare" (not "F") because it is the sheet's own admitted approximation
(documented in the spec's own Constants section, not flagged as a bug in architecture-batch2.md
§7), not something this module fixes or reproduces — it is purely a note on the unit boundary the
Tool layer must get right.
