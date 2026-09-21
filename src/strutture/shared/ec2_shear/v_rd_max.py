"""EN 1992-1-1 §6.4.5(3) maximum punching-shear stress at the column/pile face u0 (no reinforcement can
raise this limit). The governing coefficient in front of ν*fcd is a nationally-determined parameter — it is
exposed as a keyword rather than hard-coded so a National Annex value can be substituted (see
docs/divergences/ec2-shared.md: the source sheet uses an unrelated simplified 0.2*0.85/1.5 coefficient,
kept only inside the consuming `ca_punzonamento` tool under `legacy_compat=True`).

Two reviewers disagreed on which coefficient is "the" EC2 value (docs/divergences/ec2-shared.md, "Da
confermare dall'ingegnere"): EN 1992-1-1:2004's original §6.4.5(3) Note recommended `c=0.5`, adopted by
the Italian National Annex (2013) — `V_RD_MAX_COEFF_2004_NA_IT`; amendment A1:2014 lowered the
recommended value to `c=0.4` — `V_RD_MAX_COEFF_A1_2014`. Neither is hard-coded here: `coefficient`
defaults to the more conservative `V_RD_MAX_COEFF_A1_2014` (0.4), consuming tools expose it as an
explicit, named `coeff_vrd_max` choice rather than silently picking one. `alpha_cc` defaults to
`shared.materials.concrete.ALPHA_CC` (0.85, NTC2018 §4.1.2.1.1.1) for `fcd = alpha_cc*fck/gamma_c`.
Both remain overridable keywords for callers with a different National Annex value."""
from strutture.shared.materials.concrete import ALPHA_CC

from .models import VRdMax

NU_COEFFICIENT = 0.6  # EN default in nu = 0.6 * (1 - fck/250).
FCK_LIMIT_FOR_NU = 250.0
V_RD_MAX_COEFF_A1_2014 = 0.4  # EN 1992-1-1:2004/A1:2014 §6.4.5(3) recommended value (lowered from 0.5).
V_RD_MAX_COEFF_2004_NA_IT = 0.5  # EN 1992-1-1:2004 §6.4.5(3) Note + Appendice Nazionale italiana 2013.
V_RD_MAX_COEFFICIENT_EN = V_RD_MAX_COEFF_A1_2014  # deprecated alias, kept for existing importers.


def v_rd_max(
    fck_MPa: float,
    gamma_c: float = 1.5,
    *,
    alpha_cc: float = ALPHA_CC,
    coefficient: float = V_RD_MAX_COEFF_A1_2014,
) -> VRdMax:
    """vRd,max = coefficient * nu * fcd, with nu = 0.6*(1 - fck/250) and fcd = alpha_cc*fck/gamma_c."""
    if fck_MPa <= 0:
        raise ValueError(f"fck_MPa must be positive, got {fck_MPa}")
    if gamma_c <= 0:
        raise ValueError(f"gamma_c must be positive, got {gamma_c}")
    nu = NU_COEFFICIENT * (1.0 - fck_MPa / FCK_LIMIT_FOR_NU)
    fcd_MPa = alpha_cc * fck_MPa / gamma_c
    return VRdMax(v_rd_max_MPa=coefficient * nu * fcd_MPa, nu=nu, fcd_MPa=fcd_MPa)
