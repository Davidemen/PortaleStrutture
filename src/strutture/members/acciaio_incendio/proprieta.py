"""fuoco-materiali!C23:C25 — fp,θ / fy,θ / Ea,θ from Table 3.1's reduction factors.

Re-uses `strutture.shared.fire_reduction.reduction_factors` verbatim (spec §"Purpose": "this
entire tool is redundant with the existing shared module"); no interpolation is re-implemented
here."""
from strutture.shared.fire_reduction import reduction_factors

from .proprieta_models import ProprietaTemperaturaInput, ProprietaTemperaturaOutput


def proprieta_a_temperatura(inputs: ProprietaTemperaturaInput) -> ProprietaTemperaturaOutput:
    """ky,θ/kp,θ/kE,θ at `inputs.theta_C`, applied to fyk/Ea to get fy,θ/fp,θ/Ea,θ.

    `legacy_compat` has no numeric effect: the workbook's own divergence (a hardcoded
    `FORECAST.LINEAR` interpolation bracket that must be manually re-pointed per θ, see
    docs/specs/small-units.md §"Suspected bugs") is a manual-editing failure mode, not a
    deterministic function of (fyk, Ea, θ) — `interp_lookup` picks the correct bracket
    automatically in both modes, so there is nothing to reproduce."""
    factors = reduction_factors(inputs.theta_C)
    return ProprietaTemperaturaOutput(
        ky_theta=factors.ky_theta,
        kp_theta=factors.kp_theta,
        kE_theta=factors.kE_theta,
        fp_theta_MPa=inputs.fyk_MPa * factors.kp_theta,
        fy_theta_MPa=inputs.fyk_MPa * factors.ky_theta,
        ea_theta_MPa=inputs.ea_20_MPa * factors.kE_theta,
    )
