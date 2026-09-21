# Divergences — vento-cpe-rettangolare

No spreadsheet bugs identified for this tool (spec §7: "No bugs confirmed; formulas are straightforward
piecewise linear per code table"). `legacy_compat=True` and `legacy_compat=False` therefore produce
identical numeric results; the flag exists for input-model consistency across the `strutture` tool
contract but has no effect on `vento_cpe`'s calculation steps.

## Da verificare

- `B10` classification string for the mixed (per-direction) case is not given verbatim in the spec; it
  was read directly from the workbook formula (`"EDIFICIO SNELLO DIR 1"` / `"EDIFICIO SNELLO DIR 2"`) and
  confirmed against the oracle fixtures (`tests/fixtures/vento_cpe_oracle.json`, cases 3 and 4). Not a
  divergence, but flagged since it was not literally present in `docs/specs/vento.md`.
