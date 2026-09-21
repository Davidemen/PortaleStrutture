"""Step: capacity-design shear demand ("gerarchia delle resistenze"), NTC2018 §7.4.4.2.1, row Y20.

The sheet demand is MRd/H (a single resisting moment over the clear height, no overstrength
factor at all); the code-standard form (1) sums the resisting moments at both column ends
(2·MRd/H) — docs/architecture.md §7 decision D3 — and (2) applies the gamma_Rd overstrength
factor required by NTC2018 §7.4.4.2.1 (VEd = gamma_Rd * sum(MRd) / lp), 1.10 for this tool's
declared ductility class CD"B" (1.30 for CD"A"). `lp` is `h_mm`, already documented as the clear
height (`PilastroRettangolareInput.h_mm` / `PilastroCircolareInput.h_mm`). Both fixes are kept
under `legacy_compat` — see docs/divergences/ca-pilastri.md.

Not implemented (out of scope for this tool): the min(1, sum(MRb)/sum(MRc)) node-equilibrium
factor of §7.4.4.2.1, since this tool has no beam (MRb) input at all — see divergences doc.
"""
from strutture.shared.units import mm_to_m

CAPACITY_DESIGN_HINGES = 2.0  # NTC2018 §7.4.4.2.1 — momenti resistenti a entrambe le estremità
CAPACITY_DESIGN_HINGES_LEGACY = 1.0  # Y20 nel foglio originale
GAMMA_RD = 1.10  # NTC2018 §7.4.4.2.1 — fattore di sovraresistenza per CD "B" (1.30 per CD "A")
GAMMA_RD_LEGACY = 1.0  # Y20 nel foglio originale — nessun fattore di sovraresistenza applicato


def domanda_taglio_capacity_design(mrd_kNm: float, h_mm: float, *, legacy_compat: bool) -> float:
    hinges = CAPACITY_DESIGN_HINGES_LEGACY if legacy_compat else CAPACITY_DESIGN_HINGES
    gamma_rd = GAMMA_RD_LEGACY if legacy_compat else GAMMA_RD
    return gamma_rd * hinges * mrd_kNm / mm_to_m(h_mm)
