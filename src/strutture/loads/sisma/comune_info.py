"""Spec Tool 1 (`comune-lookup`, Sisma!I5/I6): `=VLOOKUP(I4,Comuni!D:J,6/7,FALSE)` → provincia/regione.

Thin wrapper over `strutture.shared.comuni`; also echoes zona sismica (not present in the sheet's
own Comuni columns, but readily available in the merged comuni-db and useful context for the user
picking ag/F0/T*C by hand). Errors (`KeyNotFound`/`AmbiguousComuneError`) are left to propagate —
the calling tool maps them to `CalcError`, matching the convention used by `strutture.loads.neve`.
"""
from strutture.shared.comuni import Comune, lookup_comune


def risolvi_comune(comune: str, provincia: str | None = None) -> Comune:
    """Resolve a comune name to its full record (regione/provincia/zona sismica/...)."""
    return lookup_comune(comune, provincia)
