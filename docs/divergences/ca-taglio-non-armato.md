# Divergences — `strutture.members.ca_taglio_non_armato`

Source: `Taglio non armato NTC2018.xlsx`, sheet `Foglio1` (`build/cellmaps/ca-taglio-non-armato/foglio1.txt`).
NTC2018 §4.1.2.3.5.1 (shear resistance without transverse reinforcement).

| cell | sheet behaviour | fixed behaviour | clause | numeric impact on golden case |
|---|---|---|---|---|
| `B17` (ρl) | `=Asl/(bw*d)`, never capped | Cap at `ρl ≤ 0.02` per §4.1.2.3.5.1 | NTC2018 §4.1.2.3.5.1 | None: golden case ρl=0.00223 is well under the cap. Verified with an oracle case (`Asl=25000, bw=1500, d=560`): sheet gives ρl=0.02976 (uncapped), fixed clamps to 0.02, reducing VRd,1 from 676.4 kN to a lower value. |

This divergence is controlled by `legacy_compat` on `TaglioNonArmatoInput` (`True` reproduces
the sheet exactly, `False` applies the fix); it has a dedicated `legacy_compat=True`/`False`
pair in `tests/members/ca_taglio_non_armato/test_fixed_behaviour.py`.

### Follow-up fix: the check must compare the RAW ratio, not the already-capped one

A reviewed finding on `compose.py` noted that the "Rapporto di armatura longitudinale entro il
limite" `Check` compared `RHO_L_MAX` against `rho_l()`'s return value — which, under
`legacy_compat=False`, is already clamped to 0.02 by `longitudinal_ratio.py`. The check could
therefore never fail in code-standard mode, silently hiding cases where the real
`Asl/(bw*d)` exceeds the §4.1.2.3.5.1 limit used to derive the formula.

Fixed by adding `longitudinal_ratio.rho_l_raw()` (uncapped) and, in `compose.run()`, checking
`rho_l_raw <= 0.02` while still feeding the capped value into VRd,1 (`taglio.rho_l` in the
output is unchanged — it is the value actually used in the formula). When the cap bites in
code-standard mode, `Report.warnings` now also gets an explicit entry naming both the raw and
the capped ρl. `legacy_compat=True` is unaffected (raw == the value already checked there);
golden and oracle cases are unaffected (their ρl is well under 0.02, so raw == capped == the
same checked value as before). See
`tests/members/ca_taglio_non_armato/test_fixed_behaviour.py::test_check_ratio_flags_uncapped_rho_l_in_code_standard_mode_too`
and `::test_run_fixed_mode_warns_when_rho_l_cap_bites`.

## Reverted: `B13` (σcp) is NOT a divergence

A previous revision of this unit divided σcp by `bw*d` in `legacy_compat=False`, treating the
sheet's `bw*h` (cellmap references `B7` "h") as a bug. That was wrong and has been reverted:
NTC2018 §4.1.2.3.5.1 defines `σcp = NEd/Ac`, where `Ac` is the FULL concrete cross-section
(`bw*h` for a rectangular web) — identical to EN1992-1-1 §6.2.2(1). Dividing by `bw*d` instead
inflates σcp by `h/d` and, through the `+0.15·σcp` term in both VRd,1 and VRd,2, inflates the
shear resistance of an unreinforced member (example: NEd=500 kN, bw=1000, h=500, d=450 gives
1.0 MPa with `bw*h` vs. an incorrectly inflated 1.111 MPa with `bw*d`, +11% on the axial term).
`sigma_cp_MPa` now always divides by `bw*h` and no longer takes a `legacy_compat` argument —
both modes agree, matching the sheet.

## Da verificare

None outside the ρl row above. `docs/architecture.md` §6 lists no entry for this unit; the
`k` size-effect cap (`k = 1+sqrt(200/d) ≤ 2`) and `σcp ≤ 0.2·fcd` cap already match the sheet
formulas and the clause text, so both are reproduced identically in both modes.

## v2 sheet (`1m`, per-metre strip) — not a divergence, an added warning

`docs/specs/small-units.md` (`ca-taglio-non-armato-v2`) and `docs/architecture-batch2.md` §4:
the `1m` sheet takes `fck` as a free input (B3) decoupled from `Rck` (B2), with no in-sheet
cross-check — a user can enter an inconsistent pair (e.g. Rck=40 → fck expected ≈33.2, but
fck=45 entered) and the sheet computes silently with the wrong fck. Both `legacy_compat` modes
now emit a `Report.warnings` entry when `|fck_MPa - 0.83*rck_MPa| / (0.83*rck_MPa) > 5%`
(`fck_consistency.avviso_incoerenza_fck_rck`); this never changes the computed VRd (same in both
modes, no numeric impact on the golden case — golden case fck=32 vs. Rck-derived 33.2 is within
tolerance, no warning). Same tool as v1 (`ca-taglio-non-armato`); `fck_MPa=None` (default)
reproduces v1's `fck=0.83*Rck` exactly. The v2 sheet's `Asl = N°*π*Ø²/4` (B13, replacing v1's
direct `Asl` input) is a UX-only input change, not a divergence: same downstream physics.
