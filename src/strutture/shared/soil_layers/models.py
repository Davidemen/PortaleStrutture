"""`SoilLayer` row model — the `strati` table input reused by the cedimenti tools (§1.2, §2)."""
from pydantic import ConfigDict, Field, model_validator

from strutture.shared.tabular import RowModel


class SoilLayer(RowModel):
    """One soil layer: depth interval `[z_top_m, z_bot_m)` measured from ground level (or from the
    foundation base, at the caller's choice — the module is depth-origin agnostic) and its
    (o)edometric modulus."""

    model_config = ConfigDict(frozen=True)

    z_top_m: float = Field(description="Profondità dal piano di riferimento, sommità dello strato", ge=0, json_schema_extra={"unit": "m"})
    z_bot_m: float = Field(description="Profondità dal piano di riferimento, base dello strato", gt=0, json_schema_extra={"unit": "m"})
    modulo_MPa: float = Field(description="Modulo (E o Eed) dello strato", gt=0, json_schema_extra={"unit": "MPa"})

    @model_validator(mode="after")
    def _bottom_below_top(self) -> "SoilLayer":
        if self.z_bot_m <= self.z_top_m:
            raise ValueError(f"lo strato ha base ({self.z_bot_m} m) non inferiore alla sommità ({self.z_top_m} m)")
        return self
