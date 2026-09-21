# Divergences — `strutture.loads.sisma`

Source: `sisma.xls`, sheet `Sisma`. `legacy_compat=True` reproduces the sheet exactly (bugs
included); `legacy_compat=False` (default) is the code-standard, fixed behaviour. The site-hazard
chain (Ss/Cc/ST/S, Cu/VR/TR, TB/TC/TD) is implemented once in `strutture.shared.ntc_site_seismic`;
its own divergences (Tabelle!E8 Ss clip, N25 case-insensitivity) are documented in
`docs/divergences/ntc-site-seismic.md` and are not repeated here.

| cell | sheet behaviour | fixed behaviour | clause | numeric impact on golden case |
|---|---|---|---|---|
| `Sisma!I45` ("coefficiente dissipativo", componente verticale η,v) | `=1/I44`, i.e. the reciprocal of q,v — not a function of ξ at all, despite the "coefficiente dissipativo" label suggesting a damping correction | Same η(ξ) formula as the horizontal component (`Sisma!I38`): `η,v = sqrt(10/(5+ξ))` | NTC2018 §7.3.3.2 | Golden case (ξ=5, q,v=1.5): sheet gives `η,v = 1/1.5 = 0.666667`; fixed gives `η,v = 1` (both cached in `tests/fixtures/... golden`/see `test_fixed_behaviour.py::test_vertical_eta_uses_damping_formula_not_1_over_qv`). This is spec §7 item 2 ("vertical component computed but unused") acted on per `docs/architecture.md` §7 open decision 4: implement q,v/η,v properly rather than leave them dead. |
| `Sisma!J` column (design spectrum Sd(T)) | No floor: the 1/T² branch (T≥TD) can decay below `0.2·ag` for large T | `Sd(T) = max(Se(T)/q, 0.2·ag)` for ULS states (SLV/SLC) | NTC2018 §3.2.3.2.1 | Golden case at `T=5 s`: sheet/legacy gives `Sd=0.00590732 g`; fixed gives `Sd = max(0.00590732, 0.2·0.098) = 0.0196 g` — a 3.3x increase (see `test_fixed_behaviour.py::test_design_spectrum_gets_0_2ag_floor_at_long_periods`). The floor starts binding around `T≈2.75 s` for the golden case's parameters; it never binds for SLO/SLD (q=1 keeps Se(T) itself well above 0.2·ag near TD, and SLE states aren't divided at all). |
| `Sisma!J55` (T=0 row) | `=N55` — literally omits the `IF(N25="slu", N/I41, N)` division that every other row (`J56:J149`) applies, so the sheet's own T=0 point is never reduced by q even under SLV/SLC | **Not a bug — reverted.** NTC18 §3.2.3.5 builds Sd(T) from the elastic-spectrum formula "sostituendo η con 1/q", not by dividing Se(T) by q. η is a plain multiplier only on `TB≤T`; on `0≤T<TB` it also sits inside the `1/(η·F0)` reciprocal term, so `Se(T)/q ≠` the eq. 3.2.4 substitution on that branch. At `T=0` the correct substitution collapses to `Sd(0)=ag·S` exactly, for any q — matching the sheet's undivided `J55` value. `valore_spettro` now computes `Sd(T) = ag·S·F0/q·(T/TB) + ag·S·(1−T/TB)` for `0≤T<TB` (both modes agree at T=0); `TB≤T` still uses `Se(T)/q`, which is algebraically identical to the substitution there | NTC2018 §3.2.3.5 eq. 3.2.4 | Golden case (SLV, q=1.5) at `T=0`: both legacy and fixed now give `Sd=0.1176 g` (see `test_fixed_behaviour.py::test_t_zero_design_value_is_not_divided_by_q_even_when_fixed`). Previously the fixed branch wrongly returned `0.0784 g` (−33%, non-conservative) by dividing by q; that was itself the real bug, now corrected. |
| `Sisma!N56:N149` (elastic spectrum, `0≤T<TB` branch) | Reciprocal term is `η·ag·S·F0·[T/TB + (1/F0)·(1−T/TB)]` — drops η from the `1/(η·F0)` term of NTC eq. 3.2.4, so `Se(0) = η·ag·S` instead of the mandatory PGA anchor `Se(0) = ag·S`. Invisible whenever ξ=5% (η=1), which is every case in the golden/oracle fixtures except one | `Se(T) = η·ag·S·F0·[T/TB + 1/(η·F0)·(1−T/TB)]` (eq. 3.2.4 verbatim); collapses to `ag·S` at T=0 for any η | NTC2018 §3.2.3.2.1 eq. 3.2.4 | For ξ=10% (η≈0.8165): legacy gives `Se(0)=0.8165·ag·S` (18% low); fixed gives `Se(0)=ag·S` exactly (see `test_spettro_elastico.py::test_fixed_t_zero_anchors_to_ag_s_regardless_of_eta` / `test_legacy_t_zero_reproduces_sheet_bug_dropping_eta_at_high_damping`, confirmed against `tests/fixtures/sisma_spettro_oracle.json` case 2, ξ=8%). Golden case (ξ=5) is unaffected in either mode. |
| `Sisma!I38` (η, damping correction) | `η = sqrt(10/(5+ξ))` with no lower bound — `xi_pct` is validated only as `gt=0`, so any ξ>28.06% gives η<0.55 | `η = max(sqrt(10/(5+ξ)), 0.55)` (`ETA_MIN` constant), applied in both modes since it is the code's own formula floor, not a spreadsheet-specific behaviour | NTC2018 §3.2.3.2.1 eq. 3.2.6 | At ξ=40%: unfloored `η≈0.4714`; floored `η=0.55` (16.7% higher, conservative). Golden case (ξ=5) unaffected (`η=1` either way). Propagates to `eta_verticale`'s fixed mode via the same `smorzamento_eta` call. |
| `Sisma!N25`, `I41`, `I40` (case compares) | Compares uppercase dropdown values (`I25`, `I40`) against lowercase literals (`"slv"`, `"slc"`, `"si"`); works only because Excel text comparison is case-insensitive | `stato_limite.is_stato_limite_uls` / `kr_regolarita.kr_regolare_altezza` normalize with `.upper()` explicitly | NTC2018 §3.2.1, §7.3.1 | None — behaviourally equivalent in both modes (confirmed against the LibreOffice oracle with a deliberately lowercase `I25="slv"`/`I40="si"` case, `tests/fixtures/sisma_fattori_struttura_oracle.json` case 6). Documented per the task note: not a bug, just an explicit normalization for a case-sensitive language. |

## Not ported (confirmed dead, per `docs/specs/sisma.md` §7 items 3-4)

- `Foglio2` sheet: references out-of-range/blank cells, produces cached `0`s and an explicit
  `#DIV/0!`. Abandoned scratch copy of the spectrum calc; not ported.
- `Tabelle!D14:D16`: orphaned duplicate Cc/Ss/ST lookups referencing cells outside the extracted
  `Sisma` range; not referenced by any of the 4 tools. Not ported.

## Da verificare

None outstanding for this package. Comune-lookup enrichment (`ComuneInfo.zona_sismica`) is a new
field not present in the sheet's own `Comuni!D:J` columns (the sheet only mirrors provincia/regione)
— it is sourced from the merged `comuni-db` (`strutture.shared.comuni`) and is additive, not a
divergence from any sheet formula.
