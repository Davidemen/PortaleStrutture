# Divergences — `strutture.shared.ntc_site_seismic`

Source: `sisma.xls`, sheet `Sisma`. `legacy_compat=True` reproduces the sheet exactly (bugs
included); `legacy_compat=False` (default) is the code-standard, fixed behaviour.

| cell | sheet behaviour | fixed behaviour | clause | numeric impact on golden case |
|---|---|---|---|---|
| `Tabelle!E8` (Ss, categoria sottosuolo B) | Clips Ss to `[0.40, 1.20]` | Clips Ss to `[1.00, 1.20]` | NTC2018 Tab. 3.2.IV | None — golden case raw value is 1.3045, clipped to the shared upper bound 1.20 either way. Divergence only manifests when `1.40 − 0.40·F0·ag < 1.00` (high `F0·ag`, e.g. `F0=2.5, ag=1.1 g` → sheet gives `Ss=0.40`, fixed gives `Ss=1.00`; confirmed against the LibreOffice oracle, see `tests/fixtures/ntc_site_seismic_parametri_sito_oracle.json` case 6). |
| `Sisma!I10` (VR = VN·Cu) | No lower bound; `VR` can fall below 35 anni for small `VN`/`Cu` | `VR = max(VN·Cu, 35)` per NTC2018 §2.4.3 | NTC2018 §2.4.3 | None — golden case `VN=50, Cu=1 → VR=50 ≥ 35` either way. Divergence manifests for small `VN`/`Cu`, e.g. `VN=10, classe=I (Cu=0.7)`: sheet/legacy gives `VR=7`, fixed gives `VR=35` (see `tests/shared/ntc_site_seismic/test_vita_riferimento.py`). |
| `Sisma!N25` (`=IF(I25="slv","slu",...)`) | Compares uppercase dropdown value against lowercase literals; works only because Excel text comparison is case-insensitive | `periodo_ritorno`/`coefficiente_uso`/`fattore_topografico_st` use `strutture.shared.tables.exact_lookup(..., ignore_case=True)` (default), so `"SLV"`/`"slv"` both resolve correctly | NTC2018 §3.2.1 | None — behaviourally equivalent in both modes; documented so a future case-sensitive rewrite doesn't silently break the lookup. |

## Da verificare

None — both suspected bugs from `docs/specs/sisma.md` §7 relevant to this module (items 1 and 5)
are confirmed against the NTC2018 text and the LibreOffice oracle, and are listed above as fixed.
Item 2 (vertical component I44/I45, unused) and item 3 (`Foglio2`, dead sheet) belong to other
tools (`fattori-struttura`) or are out of scope for this module.
