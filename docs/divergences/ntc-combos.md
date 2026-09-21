# Divergences — `strutture.shared.ntc_combos`

This shared package has no `legacy_compat` toggle of its own (it is a pure data/lookup module,
not a `Tool`); it holds NTC2018 Tab. 6.2.I/6.2.II/6.5.I partial-factor tables consumed by
downstream tools (e.g. `members/muro`).

## `gamma_g2_favorevole` was 0.0 in every column — fixed to 0.8

- **Cell/table**: `FATTORI_AZIONI` in `ntc_combos/tables.py` (Tab. 6.2.I), all three
  `ApproccioAzioni` rows (EQU/A1/A2).
- **Previous behaviour**: `gamma_g2_favorevole=0.0` in all three rows — the NTC2008 value.
- **Fixed behaviour**: `gamma_g2_favorevole=0.8` in all three rows, per NTC2018 Tab. 6.2.I/
  6.2.II §6.2.1 (raised from NTC2008's 0.0 to 0.8 for non-structural permanent loads G2 in the
  favourable case).
- **Clause**: NTC2018 Tab. 6.2.I.
- **Numeric impact**: none on any current golden/oracle case — `members/muro/combinazioni.py`
  is currently the only consumer of `fattori_azioni` and only reads the `gamma_g1_*` fields
  (see `docs/divergences/muro-sostegno.md`), so the change is latent for now but corrects the
  table for every future consumer.

## `FATTORI_RESISTENZA` (Tab. 6.5.I) was missing the "Ribaltamento" row — added

- **Table**: `FATTORI_RESISTENZA` in `ntc_combos/tables.py` and the `VerificaOpereDiSostegno`
  Literal in `ntc_combos/models.py` only listed 3 of Tab. 6.5.I's 4 rows (capacita_portante,
  scorrimento, resistenza_terreno_a_valle); "Ribaltamento" (overturning) was absent from both,
  so no γR was available for an overturning check.
- **Fixed behaviour**: added `("ribaltamento", FattoriResistenza(r1=1.0, r2=1.15, r3=1.15))` to
  `FATTORI_RESISTENZA` and `"ribaltamento"` to the `VerificaOpereDiSostegno` Literal.
- **Clause**: NTC2018 Tab. 6.5.I.
- **Numeric impact**: none on any current golden/oracle case (no current consumer calls
  `fattori_resistenza("ribaltamento")`); this only unblocks a future overturning check that
  needs a γR from this table.
