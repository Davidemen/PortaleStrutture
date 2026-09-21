"""Composes the structural steel grade lookup into one result (EN1993-1-1 §3.2)."""
from .elastic import modulo_taglio
from .models import SteelGrade, SteelProperties
from .steel import fyk_fuk
from .tables import E_MPA


def steel_properties(grado: SteelGrade, t_mm: float, *, legacy_compat: bool = False, e_MPa: float = E_MPA) -> SteelProperties:
    """Full mechanical property set for a structural steel grade at a given thickness."""
    fyk_mpa, fuk_mpa = fyk_fuk(grado, t_mm, legacy_compat=legacy_compat)
    return SteelProperties(
        grado=grado,
        t_mm=t_mm,
        fyk_MPa=fyk_mpa,
        fuk_MPa=fuk_mpa,
        e_MPa=e_MPa,
        g_MPa=modulo_taglio(e_MPa),
    )
