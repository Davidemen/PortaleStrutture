"""EN1993-1-1 Table 3.1 — fyk/fuk by grade and thickness band."""
from strutture.shared.divergences import legacy
from strutture.shared.tables import KeyNotFound, exact_lookup

from .models import SteelGrade
from .tables import SPESSORE_LIMITE_MASSIMO_MM, SPESSORE_LIMITE_SOTTILE_MM, STEEL_TABLE_MPA


def fyk_fuk(grado: SteelGrade, t_mm: float, *, legacy_compat: bool = False) -> tuple[float, float]:
    """(fyk, fuk), MPa. `legacy_compat=True` always returns the t<=40mm band, ignoring `t_mm`
    (acciaio-colonne-ec3!Materiali never reads element thickness)."""
    thin_band, thick_band = exact_lookup(STEEL_TABLE_MPA, grado)
    if legacy("materials/acciaio-strutturale-fascia-spessore-ignorata", legacy_compat):
        return thin_band
    if t_mm <= SPESSORE_LIMITE_SOTTILE_MM:
        return thin_band
    if t_mm <= SPESSORE_LIMITE_MASSIMO_MM:
        return thick_band
    raise KeyNotFound(f"t_mm={t_mm} outside EN1993-1-1 Tab. 3.1 range (0, {SPESSORE_LIMITE_MASSIMO_MM}]")
