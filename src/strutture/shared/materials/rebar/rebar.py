"""Composes the rebar grade lookup into one result (NTC2018 §11.3.2)."""
from strutture.shared.tables import exact_lookup

from .fyd import fyd
from .models import RebarGrade, RebarProperties
from .tables import CURRENT_NTC_GRADES, ES_MPA, GAMMA_S, REBAR_TABLE_MPA


def rebar_properties(grado: RebarGrade, *, gamma_s: float = GAMMA_S, es_MPa: float = ES_MPA) -> RebarProperties:
    """Full mechanical property set for a rebar grade."""
    fyk_mpa, ftk_mpa, sigma_amm_mpa = exact_lookup(REBAR_TABLE_MPA, grado)
    return RebarProperties(
        grado=grado,
        fyk_MPa=fyk_mpa,
        ftk_MPa=ftk_mpa,
        fyd_MPa=fyd(fyk_mpa, gamma_s=gamma_s),
        es_MPa=es_MPa,
        sigma_amm_MPa=sigma_amm_mpa,
        legacy_grade=grado not in CURRENT_NTC_GRADES,
    )
