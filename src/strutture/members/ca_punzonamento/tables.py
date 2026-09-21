"""Lookup tables mined from `Shotblast_225N` (docs/specs/ca-punzonamento.md, "Lookup tables").

Pure data only — no functions, no I/O, no mutation.
"""
from typing import Literal

PosizionePilastro = Literal["centrato", "interno", "bordo", "angolo"]

# EC2§6.4.3(6) fig. 6.21N — dropdown H13:K13, exact-match, no interpolation.
POSIZIONE_BETA: tuple[tuple[PosizionePilastro, float], ...] = (
    ("centrato", 1.0),   # H13 — pilastro centrato, carico assialsimmetrico, nessuna eccentricità
    ("interno", 1.15),   # I13 — pilastro interno con eccentricità
    ("bordo", 1.4),      # J13 — pilastro di bordo
    ("angolo", 1.5),     # K13 — pilastro d'angolo
)

# D55 dropdown, flat enum (not a range table). Sheet validation list is "8,10,12,14,16,28,20,22":
# 28 is a likely typo for 18 (docs/specs/ca-punzonamento.md §7.1) — kept only for legacy_compat=True.
PHI_STAFFA_OPTIONS_MM: tuple[float, ...] = (8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0)
PHI_STAFFA_LEGACY_TYPO_MM = 28.0
PHI_STAFFA_LEGACY_FIX_MM = 18.0

# Grade baked into the sheet's Asw,min formula (0.08*sqrt(fck)*sr*st/(450*1.5), fyk=450 hardcoded) and
# fywd,ef cap (EC2 eq. 6.52) — the sheet has no rebar-grade input, so B450C (current NTC2018 grade,
# fyk=450 MPa) is used for both, matching the sheet's own baked-in numbers.
STAFFA_GRADE = "B450C"

# Search table AO2:AX152 (step 5): a/d in [0.5, 2.0], step 0.01, 151 samples.
SCAN_A_SU_D_MIN = 0.5
SCAN_A_SU_D_MAX = 2.0
SCAN_A_SU_D_STEP = 0.01
