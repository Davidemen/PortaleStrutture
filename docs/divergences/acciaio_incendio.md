# Divergences — `acciaio-resistenza-incendio`

| Cell | Sheet behaviour | Fixed behaviour | Clause | Numeric impact on golden case |
|---|---|---|---|---|
| `resistenza!D5` | `=IF(D2="s235",360,IF(D3="s275",430,510))` — 2nd condition tests `D3` (=210000, the elastic modulus number) instead of `D2` (the grade). `D3` is never `"s275"`, so the branch never fires and **S275 always gets fu(20°C)=510 MPa** (S355's value). | Tests `D2` as intended: S235→360, S275→430, S355→510 MPa. | EN10025 nominal fu — S275 | Golden case uses default grade S355, unaffected (fu=510 in both modes). For S275: legacy fu(20°C)=510 → fu,θ at t=5min = 276.995 MPa; fixed fu(20°C)=430 → fu,θ = 233.545 MPa (−15.7%). |

## Kept as-is (documented, not a bug)

- **Steel temperature ≡ gas temperature.** The sheet has no Am/V section factor and no protection
  material term — it treats the exposed steel as instantaneously at the ISO 834 gas temperature
  (no thermal lag). This is the simplified unprotected-steel nomogram approach the sheet was built
  for, not a full EN1991-1-2 heat-transfer analysis; kept in both modes. The tool always emits a
  warning in the `Report` (`acciaio_incendio/tool.py: NO_THERMAL_LAG_WARNING`) so users don't
  mistake it for a protected-section calculation.
- **fu,θ reuses ky,θ** (the yield-strength reduction factor) rather than a dedicated ultimate-
  strength factor — EN1993-1-2 Table 3.1 doesn't tabulate one, so this is standard practice.
- Case-insensitive grade text compare (`"s235"` vs dropdown `"S235"`) — matches Excel's default
  string comparison; not a bug.

# Divergences — `acciaio-proprieta-temperatura`

No numeric divergence: `legacy_compat` is present per the tool contract but is a no-op — every
mode calls `strutture.shared.fire_reduction.reduction_factors` (generic `interp_lookup`), which
picks the correct Table 3.1 bracket automatically for any θ in [20, 1200] °C.

## Kept as-is (documented, not a bug)

- **`fuoco-materiali`'s own workbook bug is not reproducible as a mode toggle.** Each of its four
  θ sheets (550/600/650/700 °C) computes `fp,θ`/`fy,θ`/`Ea,θ` via `FORECAST.LINEAR` against a
  *hardcoded* 2-row bracket (e.g. `D11:D12,B11:B12` for the 550°C sheet) that the sheet's own
  comment says "must be manually re-pointed" if θ is changed — a data-entry failure mode, not a
  deterministic function of (fyk, Ea, θ). At each sheet's own fixed θ the bracket happens to be
  correct, so all four oracle cases match the shared module exactly in both modes
  (`tests/fixtures/acciaio_incendio_proprieta_oracle.json`). Re-implementing via
  `strutture.shared.tables.interp_lookup` (bracket picked automatically, raises `KeyNotFound`
  outside [20, 1200] °C) eliminates this class of bug entirely for any θ the tool is ever asked
  to run — that is why this tool consumes the shared module verbatim instead of porting the
  `FORECAST.LINEAR` formula.
