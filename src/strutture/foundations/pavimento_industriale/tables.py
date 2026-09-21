"""Tool-local lookup tables (single consumer, promote to `shared/tables` on a second consumer per
BUILD_CONTRACT `## Tool packages`): the `Winkler` subgrade table and the position-dependent
Westergaard/EC2 constants of `carichi_distribuiti_concentrati`."""
from typing import Literal

from .carico_row import PosizioneCarico

SottofondoTipo = Literal["soffice", "mediocre", "materiale di riporto costipato", "molto costipato"]

# `Winkler!A2:C5` — subgrade type -> k' = k/100 [N/mm3] (column B "k" [N/cm3] is not used downstream).
WINKLER_K_PRIME_N_MM3: tuple[tuple[SottofondoTipo, float], ...] = (
    ("soffice", 0.015),
    ("mediocre", 0.03),
    ("materiale di riporto costipato", 0.06),
    ("molto costipato", 0.1),
)

# Westergaard point-load stress coefficients per position (spec "Tool: pav-carichi-concentrati",
# calculation step 4). `centro`/`bordo` use (k1, k2): sigma = k1*(P*1000)/h^2*(log10(l/b)+k2).
# `spigolo` uses (k1, k3, k4): sigma = k1*(P*1000)/h^2*(1-k3*(rr/l)^k4).
WESTERGAARD_CENTRO = (1.264, 0.267)
WESTERGAARD_BORDO = (2.288, 0.09)
WESTERGAARD_SPIGOLO = (3.0, 1.23, 0.6)

# Punching enhancement factor beta per position (spec "Tool: pav-carichi-concentrati" inputs L27:N27).
BETA_PUNZONAMENTO: dict[PosizioneCarico, float] = {"centro": 1.15, "bordo": 1.4, "spigolo": 1.5}

# Westergaard equivalent-radius correction threshold (spec calculation step 2).
RADIUS_CORRECTION_THRESHOLD = 1.724

# Crack-check tensile-strength de-rating factor (spec calculation step 9/11; clause unverified,
# architecture-batch2.md §7 `pavimento I39` flags the nearby joint-check label as "Da verificare"
# for the same reason -- kept as-is both modes, see docs/divergences/pavimento-industriale.md).
CRACK_DERATING_FACTOR = 1.2

# Mesh reinforcement lever-arm factor (spec calculation step 11 "As=...", "Mrd=As*0.9*d*fyd/1000").
REBAR_LEVER_ARM_FACTOR = 0.9

# daN/m² -> kN/m² (spec "Tool: pav-carichi-distribuiti" step 1); not in `shared/units` yet (single
# consumer so far -- flagged in this package's final notes for promotion).
DAN_PER_KN_M2 = 100.0
