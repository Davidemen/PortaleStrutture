"""Step (spec calc steps 6-8, `Neve accumulo!K32/K35/H36`): wind-redistribution shape coeff μw."""
from typing import Final

from strutture.shared.numeric import clamp

# Circ. 2019 §C3.4.5.6 (mirroring EN1991-1-3 §6.2(3)): 0.8 <= mu_w <= 4.0. Both bounds are part of
# the sheet's own `H36` formula (`docs/specs/neve.md` step 8), so they are applied identically in
# legacy and code-standard mode — this is not a legacy_compat divergence, see docs/divergences/neve.md.
MW_MIN: Final[float] = 0.8
MW_MAX: Final[float] = 4.0


def rapporto_gamma_h_qsk(gamma_kn_m2: float, h_m: float, qsk_kn_m2: float) -> float:
    """`K32` = γ·h/qsk."""
    return gamma_kn_m2 * h_m / qsk_kn_m2


def mu_w_grezzo(b1_m: float, b2_m: float, h_m: float, gamma_h_over_qsk: float) -> float:
    """`K35` = min((b1+b2)/(2h), γh/qsk)."""
    return min((b1_m + b2_m) / (2 * h_m), gamma_h_over_qsk)


def mu_w(mu_w_raw: float) -> float:
    """`H36` = clamp(K35, MW_MIN, MW_MAX) — Circ. 2019 §C3.4.5.6 / EN1991-1-3 §6.2(3): 0.8 <= mu_w
    <= 4.0, applied the same way regardless of `legacy_compat` (see module-level comment above).
    """
    return clamp(mu_w_raw, MW_MIN, MW_MAX)
