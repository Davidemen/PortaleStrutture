"""Material properties (`Mensola tozza!Z5:Z9`): fyd, fcd (NTC2018 §4.1.2.1.1.1, Tab. 4.1.V).

`Z7` (labelled "fyk", actually computes ftk) is dead — no downstream formula references it (spec
§7) — and is intentionally not reproduced here, even in `legacy_compat=True` mode.

Bug (confirmed against the workbook, not just spec §7): `Tabelle!M45:P49` holds only
B450C/B500C/FeB32k/FeB38k/FeB44k, but `H14`'s dropdown (`BU16:BU20`) offers `FeB22k` instead of
`B500C`. Selecting `FeB22k` therefore makes the real sheet's VLOOKUP return `#N/A` (`Z7`, `Z8`,
`H28`, `H33`, `C34` all become `#N/A`). `legacy_compat=True` reproduces this exactly by raising;
`legacy_compat=False` fixes it via the shared union rebar table (merge C1, which does carry
FeB22k) — see `docs/divergences/ca-mensole.md`.
"""
from strutture.shared.divergences import legacy
from strutture.shared.materials.concrete import GAMMA_C, concrete_properties
from strutture.shared.materials.rebar import GAMMA_S, rebar_properties
from strutture.shared.report import CalcError
from strutture.shared.tables import KeyNotFound

from .models import ClasseCalcestruzzoMensola, GradoAcciaioMensola, MaterialiResult

_STEEL_MISSING_FROM_LOCAL_TABLE: GradoAcciaioMensola = "FeB22k"


def materiali(
    acciaio: GradoAcciaioMensola, calcestruzzo: ClasseCalcestruzzoMensola, *, legacy_compat: bool
) -> MaterialiResult:
    """fyd = fyk/γs, fcd = 0.85·fck/γc (`legacy_compat=True` uses the sheet's fck fill-down bug,
    see `strutture.shared.materials.concrete.fck`)."""
    if legacy("ca-mensole/acciaio-feb22k-mancante-in-tabella", legacy_compat) and acciaio == _STEEL_MISSING_FROM_LOCAL_TABLE:
        raise CalcError(
            "Combinazione acciaio=FeB22k con legacy_compat=True: il foglio originale restituisce "
            "#N/A perché Tabelle!M45:P49 non contiene la riga FeB22k (vedi docs/divergences/ca-mensole.md)"
        )
    try:
        rebar = rebar_properties(acciaio)
        concrete = concrete_properties(calcestruzzo, legacy_compat=legacy_compat)
    except KeyNotFound as error:
        raise CalcError(str(error)) from error
    return MaterialiResult(gamma_s=GAMMA_S, gamma_c=GAMMA_C, fyd_MPa=rebar.fyd_MPa, fcd_MPa=concrete.fcd_MPa)
