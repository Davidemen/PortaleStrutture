"""Step: material properties (docs/specs/fond-plinti-pali.md `AG6/AG7`), reusing `shared.materials`
(never re-derive fck/fyd formulas here).

Unlike `plinti_isolati` (and every `ca_*` member tool), the pile-cap sheet takes `fck` as a plain
literal input (`AG7 "f'c = fck" = 32 N/mm2`), not derived from a cube strength `Rck` via a class
table. `concrete_properties`'s own `legacy_compat` toggles that Rck->fck approximation
(docs/divergences/materials.md) — a different workbook's quirk, unrelated to this tool's own
`legacy_compat` (which only reproduces `Footing check`'s bugs). So `classe_calcestruzzo` is always
resolved with `legacy_compat=False` here, giving the class's own literal fck regardless of this
tool's mode."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.materials.concrete import ConcreteClass, ConcreteProperties, concrete_properties
from strutture.shared.materials.rebar import RebarGrade, RebarProperties, rebar_properties


class Materiali(BaseModel):
    """Concrete and rebar mechanical properties used by the flexural/strut-tie/shear design."""

    model_config = ConfigDict(frozen=True)

    calcestruzzo: ConcreteProperties = Field(description="Proprietà del calcestruzzo")
    acciaio: RebarProperties = Field(description="Proprietà dell'acciaio da armatura")


def materiali(classe_calcestruzzo: ConcreteClass, grado_acciaio: RebarGrade, gamma_s: float) -> Materiali:
    return Materiali(
        calcestruzzo=concrete_properties(classe_calcestruzzo, legacy_compat=False),
        acciaio=rebar_properties(grado_acciaio, gamma_s=gamma_s),
    )
