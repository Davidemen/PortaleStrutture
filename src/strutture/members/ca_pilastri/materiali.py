"""Step: material design properties (NTC2018 Tab.4.1.V / §4.1.2.1.1.1 / §4.1.2.1.1.3), sourced
from the shared `Tabelle!M45:P49` (steel) / `Tabelle!M34:O41` (concrete) lookups (rows 2-4)."""
from strutture.shared.materials.concrete import concrete_properties
from strutture.shared.materials.rebar import rebar_properties

from .models import AcciaioGrado, ClsClasse, MaterialiResult

GAMMA_S = 1.15  # Z5 (NTC2018 Tab. 4.1.V)
GAMMA_C = 1.5  # Z6 (NTC2018 Tab. 4.1.V)
ALPHA_CC = 0.85  # NTC2018 §4.1.2.1.1.1


def proprieta_materiali(acciaio: AcciaioGrado, cls: ClsClasse, *, legacy_compat: bool) -> MaterialiResult:
    """Z7 (ftk, mislabeled "fyk" in the sheet, unused downstream), Z8 (fyd), Z9 (fcd)."""
    rebar = rebar_properties(acciaio, gamma_s=GAMMA_S)
    concrete = concrete_properties(cls, legacy_compat=legacy_compat, gamma_c=GAMMA_C, alpha_cc=ALPHA_CC)
    return MaterialiResult(fyd_MPa=rebar.fyd_MPa, fcd_MPa=concrete.fcd_MPa, ftk_non_usato_MPa=rebar.ftk_MPa)
