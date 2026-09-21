# Divergences — `strutture.shared.comuni`

Source: `sisma.xls`/`vento.xls` (byte-identical `Comuni` sheets) and `neve.xls` (its own, newer/
otherwise inconsistent snapshot), per `docs/architecture.md` §3 conflict C3. Unlike the calculation
tools, this module has no `legacy_compat` toggle: it produces a single merged, validated
`data/comuni.csv` and the three sheet snapshots disagree with *each other*, not with a "correct"
formula — the merge rule below is the resolution, applied unconditionally.

| column | sheet behaviour | merged behaviour | clause/source | numeric impact on golden cases |
|---|---|---|---|---|
| `Provincia` | sisma/vento hold the old name (e.g. "Milano" for what is now "Monza e Brianza"); neve holds 105 renamed rows | Take `Provincia` from the **neve** snapshot (newer) | architecture.md §3 C3 | None on the three spec golden comuni (Brembate/Mapello/Bergamo/Milano — all pre-2009 provinces, unaffected by the Monza e Brianza split); affects e.g. Agrate Brianza (`Provincia`: "Monza" → "Monza e Brianza"). |
| `Vento` (zone 1–9) | neve's copy holds the invalid literal `56` on 377/8101 rows (corrupted collapse of zones 5 and 6) | Take `Vento` from the **sisma/vento** snapshot (always a valid `1..9` value in the source data) | architecture.md §3 C3 | None on the golden comuni (their sisma/vento/neve Vento values already agree); the validator (`zona_vento ∈ 1..9`) would fail the build if this rule were reversed, since `56` is out of domain — confirmed via `tests/shared/comuni/test_merge.py::test_merge_ignores_invalid_vento_literal_in_neve_snapshot`. |
| `Neve` (zona I alpina/I mediterranea/II/III) | sisma/vento's copy has 26 blank rows (never filled in); neve's copy has none | Take `Neve` zone from the **neve** snapshot | architecture.md §3 C3 | None on the golden comuni (all three golden cases already had a Neve zone in every snapshot). |
| `Regione`, `Codice Istat`, `Comune`, `Sismica` | byte-identical across all three snapshots | Take from the **sisma/vento** snapshot (arbitrary since identical); build asserts identity and fails loudly if a future snapshot update introduces drift | architecture.md §3 C3 | None. |

## Da verificare

None. All three column-level conflicts documented in `docs/architecture.md` §3 (C3) were
re-verified directly against `build/data/{sisma,vento,neve}/comuni.csv` while building this module
(377/8101 corrupt `Vento=56` rows in neve, 495/8101 `Neve` differences, 26 blanks in sisma's `Neve`
column, 105 `Provincia` renames in neve, 0 diffs on `Regione`/`Codice Istat`/`Comune`/`Sismica`) —
counts match the architecture doc exactly, so the merge rule is applied as specified, not as a
guess.
