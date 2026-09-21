"""Range checks for the manual site-hazard inputs ag/F0/T*C (Sisma!I28:I30, spec Tool 3).

These three are not computed by the workbook: they are normally read off the INGV national
seismic-hazard grid for the comune/TR pair (`docs/specs/sisma.md` "Upstream" section, and
`docs/architecture.md` §7 open decision 2). No reticolo lookup exists here, so this module only
guards against transcription errors — bounds are the plausible envelope of the published INGV grid
for the Italian territory, not a hard NTC clause.
"""
from typing import Final

from strutture.shared.report import CalcError

AG_MIN_G: Final[float] = 0.01
AG_MAX_G: Final[float] = 1.00
F0_MIN: Final[float] = 1.00
F0_MAX: Final[float] = 5.00
TC_STAR_MIN_S: Final[float] = 0.01
TC_STAR_MAX_S: Final[float] = 2.00


def valida_parametri_sito(ag_g: float, f0: float, tc_star_s: float) -> None:
    """Raises `CalcError` (Italian message) if ag/F0/T*C fall outside the plausible INGV envelope."""
    if not AG_MIN_G <= ag_g <= AG_MAX_G:
        raise CalcError(f"ag={ag_g} g fuori dal range plausibile [{AG_MIN_G}, {AG_MAX_G}] g")
    if not F0_MIN <= f0 <= F0_MAX:
        raise CalcError(f"F0={f0} fuori dal range plausibile [{F0_MIN}, {F0_MAX}]")
    if not TC_STAR_MIN_S <= tc_star_s <= TC_STAR_MAX_S:
        raise CalcError(f"T*C={tc_star_s} s fuori dal range plausibile [{TC_STAR_MIN_S}, {TC_STAR_MAX_S}] s")
