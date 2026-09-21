"""Generic RC section engine (pure, no `Tool` registered here): arbitrary polygon outline +
point-area bars, NTC 2018 §4.1.2.1.2.1 concrete/steel constitutive laws, strip integration of a
strain plane. See `docs/architecture-phase4.md` §A for the design and every module's docstring
for the sign convention. Consumed by `strutture.members.ca_sezione_mn` (Phase 4 part B/C)."""
