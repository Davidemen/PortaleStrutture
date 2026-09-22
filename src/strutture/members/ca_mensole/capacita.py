"""Strut-and-tie capacities (`Mensola tozza!H28,H30,H31,H32,H33`, spec §4 steps 12-16).

`H30` returns the *string* `"1.5"` on the sheet's SI branch and the *number* `1` on the NO branch
(spec §7). Excel auto-coerces the string, so the numeric result is identical either way; this
reimplements `H30` as a plain number in both `legacy_compat` modes (no numeric impact, see
`docs/divergences/ca-mensole.md`).
"""
import math

from strutture.shared.divergences import legacy
from strutture.shared.units import kn_to_n, n_to_kn

from .models import CapacitaResult, SiNo

STAFFE_VERTICALI_C = 1.5   # c = 1.5 when H29="SI" — clause "?" (spec §6)
STAFFE_ASSENTI_C = 1.0     # c = 1 when H29="NO"
LEVER_ARM_FACTOR = 0.9     # internal lever arm 0.9d (standard flexure convention, spec §6)
STRUT_EFFECTIVENESS_COEFF = 0.4     # ν-like strut effectiveness coefficient in PRC — clause "?" (spec §6)
INCLINED_CONTRIBUTION_REDUCTION = 0.8  # empirical reduction on ΔPR's contribution to PR (spec §6)


def coefficiente_c(staffe_verticali: SiNo) -> float:
    """`H30` — amplification coefficient when vertical stirrups are present."""
    return STAFFE_VERTICALI_C if staffe_verticali == "SI" else STAFFE_ASSENTI_C


def capacita(
    as_hor_mm2: float,
    as_incl_mm2: float,
    fyd_MPa: float,
    hed_kN: float,
    d_mm: float,
    l_mm: float,
    b_mm: float,
    fcd_MPa: float,
    c_coeff: float,
    angolo_incl_deg: float,
    legacy_compat: bool = False,
) -> CapacitaResult:
    """PRS (tie), PRC (strut), ΔPR (inclined bars), PR = min(PRS + 0.8·ΔPR, PRC).

    The sheet compares PEd with the uncapped sum PRS + 0.8·ΔPR and checks the strut only against
    PRS: with inclined bars the corbel could pass both while the strut is overloaded (proof-read
    finding, non-conservative by up to 0.8·ΔPR). Excel mode keeps the sheet (register:
    ca-mensole/capacita-globale-non-limitata-dal-puntone)."""
    prs_kN = n_to_kn((as_hor_mm2 * fyd_MPa - kn_to_n(hed_kN)) * LEVER_ARM_FACTOR * d_mm / l_mm)
    prc_kN = n_to_kn(
        STRUT_EFFECTIVENESS_COEFF * b_mm * d_mm * fcd_MPa * c_coeff / (1 + (l_mm / (LEVER_ARM_FACTOR * d_mm)) ** 2)
    )
    dpr_kN = n_to_kn(as_incl_mm2 * fyd_MPa * math.sin(math.radians(angolo_incl_deg)))
    pr_kN = prs_kN + INCLINED_CONTRIBUTION_REDUCTION * dpr_kN
    if not legacy("ca-mensole/capacita-globale-non-limitata-dal-puntone", legacy_compat):
        pr_kN = min(pr_kN, prc_kN)
    return CapacitaResult(c_coeff=c_coeff, prs_kN=prs_kN, prc_kN=prc_kN, dpr_kN=dpr_kN, pr_kN=pr_kN)
