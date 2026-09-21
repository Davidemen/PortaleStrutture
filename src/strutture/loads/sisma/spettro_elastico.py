"""NTC 2018 §3.2.3.2.1 eq. 3.2.4-3.2.7 — horizontal elastic response spectrum ordinate Se(T)
(Sisma!N column).

Sisma!N56:N149 (0<=T<TB branch) drops η from the reciprocal term: `η·ag·S·F0·[T/TB + (1/F0)·
(1−T/TB)]` instead of NTC eq. 3.2.4's `η·ag·S·F0·[T/TB + 1/(η·F0)·(1−T/TB)]`. At T=0 the sheet
therefore gives `Se(0)=η·ag·S` instead of the mandatory PGA anchor `Se(0)=ag·S`; invisible at ξ=5%
(η=1) but wrong for any other damping. Documented in `docs/divergences/sisma.md`.
"""


def se_elastico(
    t_s: float, tb_s: float, tc_s: float, td_s: float, ag_g: float, s: float, f0: float, eta: float, *, legacy_compat: bool
) -> float:
    """Se(T), g. Four branches: rising ramp, constant plateau, 1/T decay, 1/T² decay."""
    if t_s < 0:
        raise ValueError(f"periodo T={t_s} non può essere negativo")
    if t_s < tb_s:
        if legacy_compat:
            return eta * ag_g * s * f0 * (t_s / tb_s + (1.0 / f0) * (1.0 - t_s / tb_s))  # Sisma!N56:N149 bug: drops η
        return eta * ag_g * s * f0 * (t_s / tb_s + (1.0 / (eta * f0)) * (1.0 - t_s / tb_s))
    if t_s < tc_s:
        return eta * ag_g * s * f0
    if t_s < td_s:
        return eta * ag_g * s * f0 * (tc_s / t_s)
    return eta * ag_g * s * f0 * (tc_s * td_s / t_s**2)
