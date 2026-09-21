"""Step: geometric summary of the section (Ac, As, rho), reusing `shared.sezione_ca.geometria.area`
rather than re-deriving the polygon area (docs/architecture-phase4.md §A/§B)."""
from strutture.shared.sezione_ca.geometria import area as area_poligono
from strutture.shared.sezione_ca.modelli import Sezione

from .models_output import GeometriaOutput


def riepilogo_geometrico(sezione: Sezione) -> GeometriaOutput:
    ac_mm2 = area_poligono(sezione.contorno)
    as_mm2 = sum(barra.area_mm2 for barra in sezione.barre)
    rho = as_mm2 / ac_mm2 if ac_mm2 > 0.0 else 0.0
    return GeometriaOutput(ac_mm2=ac_mm2, as_mm2=as_mm2, rho=rho, n_barre=len(sezione.barre))
