"""Tool 0 — materiali-cls-acciaio: risoluzione delle proprietà dei materiali per la trave.

Riusa `strutture.shared.materials.concrete/rebar` (già validati a monte); non duplica le
tabelle NTC2018 Tab. 4.1.I / §11.3.2.
"""
from strutture.shared.materials.concrete import ConcreteClass, concrete_properties
from strutture.shared.materials.rebar import RebarGrade, rebar_properties

from .models import MaterialiOutput


def materiali_trave(tipo_cls: ConcreteClass, tipo_acciaio: RebarGrade, *, legacy_compat: bool = False) -> MaterialiOutput:
    """Proprietà di calcestruzzo e acciaio per la trave (Tabelle!M34:R41, M45:P50)."""
    calcestruzzo = concrete_properties(tipo_cls, legacy_compat=legacy_compat)
    acciaio = rebar_properties(tipo_acciaio)
    return MaterialiOutput(calcestruzzo=calcestruzzo, acciaio=acciaio)
