"""NTC 2018 §3.2.3.5 eq. 3.2.4 (η→1/q substitution) — design spectrum ordinate Sd(T) (Sisma!J
column).

Sisma!J56:J149 = `IF(N25="slu", N/I41, N)`: divides the elastic ordinate by q only for the ultimate
limit states (SLV/SLC); serviceability states (SLO/SLD) use the elastic ordinate unreduced.

NTC18 §3.2.3.5 builds Sd(T) from the elastic spectrum formula "sostituendo η con 1/q", not by
dividing Se(T) by q. On the TB≤T branches that substitution is algebraically identical to Se(T)/q
(η only appears as a linear multiplier there), so `se_g / q` is correct for those. On 0≤T<TB, η
also appears inside the `1/(η·F0)` reciprocal term, so substituting η=1/q there is NOT the same as
dividing by q: `Sd(T) = ag·S·F0/q·(T/TB) + ag·S·(1−T/TB)`. At T=0 this collapses to `Sd(0) = ag·S`
exactly, for any q — matching the sheet's own `Sisma!J55 = =N55` (undivided). That cell is
code-compliant, not a bug: both legacy and fixed modes agree at T=0 (see
`docs/divergences/sisma.md`).

Two real divergences from the sheet coexist in the same undivided legacy body: the missing floor
"Sd(T) non può essere inferiore a 0.2·ag" (binds at large T), and, on 0≤T<TB, the rising-branch
formula itself — `se_g / q` (sheet) vs. the η→1/q substitution above (fixed), see
`sisma/spettro-progetto-salita-eta-sostituita-da-1-q` in the register.
"""
from typing import Final

from strutture.shared.divergences import legacy

DESIGN_SPECTRUM_FLOOR_RATIO: Final[float] = 0.2  # NTC2018 §3.2.3.2.1: Sd(T) >= 0.2·ag (SLV/SLC)


def valore_spettro(
    se_g: float,
    q: float,
    t_s: float,
    *,
    is_uls: bool,
    ag_g: float,
    s: float,
    f0: float,
    tb_s: float,
    eta: float,
    legacy_compat: bool,
) -> float:
    """Sd(T) for ULS states (SLV/SLC), Se(T) unreduced for SLE states (SLO/SLD).

    `eta` is the damping correction already inside `se_g`: NTC2018 §3.2.3.5 builds the design
    spectrum by SUBSTITUTING η with 1/q, so every ULS branch must drop it — the sheet divides the
    elastic ordinate (η included) by q, identical only at ξ = 5 % (register:
    sisma/spettro-progetto-plateau-eta-non-sostituita)."""
    if not is_uls:
        return se_g
    # This single branch also implements sisma/spettro-progetto-salita-eta-sostituita-da-1-q (the
    # sheet doesn't separate the missing 0.2*ag floor from the 0<=T<TB formula, so there is no
    # second legacy() call here; see that entry, ramo="nessuno").
    if legacy("sisma/spettro-progetto-senza-pavimento-0-2ag", legacy_compat):
        if t_s == 0.0:
            return se_g  # Sisma!J55: the T=0 row skips the SLU division applied everywhere else
        return se_g / q
    sd_g = _sd_uls(se_g, q, t_s, ag_g=ag_g, s=s, f0=f0, tb_s=tb_s, eta=eta)
    return max(sd_g, DESIGN_SPECTRUM_FLOOR_RATIO * ag_g)


def _sd_uls(se_g: float, q: float, t_s: float, *, ag_g: float, s: float, f0: float, tb_s: float, eta: float) -> float:
    """Unfloored Sd(T), NTC18 eqs. 3.2.4-3.2.7 with η replaced by 1/q on EVERY branch: above T_B the
    elastic ordinate is η·a_g·S·F_0·(…), so dividing it by η·q gives a_g·S·F_0·(…)/q — continuous
    with the rising branch at T_B (the old `se_g / q` kept η and stepped down by it at T_B)."""
    if t_s < tb_s:
        return ag_g * s * f0 / q * (t_s / tb_s) + ag_g * s * (1.0 - t_s / tb_s)
    return se_g / eta / q
