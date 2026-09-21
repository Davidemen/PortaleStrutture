"""Step: material properties (docs/specs/fond-plinti-isolati.md Tool-2 step 7), reusing
`shared.materials` (never re-derive fck/fyd formulas here)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.materials.concrete import ConcreteClass, ConcreteProperties, concrete_properties
from strutture.shared.materials.rebar import RebarGrade, RebarProperties, rebar_properties


class Materiali(BaseModel):
    """Concrete and rebar mechanical properties used by the flexural/SLS design."""

    model_config = ConfigDict(frozen=True)

    calcestruzzo: ConcreteProperties = Field(description="Proprietà del calcestruzzo")
    acciaio: RebarProperties = Field(description="Proprietà dell'acciaio da armatura")


def materiali(classe_calcestruzzo: ConcreteClass, grado_acciaio: RebarGrade, gamma_s: float, *,
              legacy_compat: bool) -> Materiali:
    """Material properties for the flexural design and SLS stress checks."""
    return Materiali(
        calcestruzzo=concrete_properties(classe_calcestruzzo, legacy_compat=legacy_compat),
        acciaio=rebar_properties(grado_acciaio, gamma_s=gamma_s),
    )
