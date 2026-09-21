"""Literal type and frozen result model for the concrete class table (NTC2018 §4.1.2.1.1, Tab. 4.1.I)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ConcreteClass = Literal[
    "C8/10", "C12/15", "C16/20", "C20/25", "C25/30", "C28/35",
    "C30/37", "C32/40", "C35/45", "C40/50", "C45/55", "C50/60",
]


class ConcreteProperties(BaseModel):
    """Mechanical properties of a concrete class (ca-fessurazione!MATERIALE CLS, ca-travi/mensole/pilastri!Tabelle M34:R41)."""

    model_config = ConfigDict(frozen=True)

    classe: ConcreteClass = Field(description="Classe di resistenza del calcestruzzo")
    rck_MPa: float = Field(description="Resistenza cubica caratteristica Rck", json_schema_extra={"unit": "MPa"}, gt=0)
    fck_MPa: float = Field(description="Resistenza cilindrica caratteristica fck", json_schema_extra={"unit": "MPa"}, gt=0)
    fcm_MPa: float = Field(description="Resistenza cilindrica media fcm", json_schema_extra={"unit": "MPa"}, gt=0)
    ecm_MPa: float = Field(description="Modulo elastico secante Ecm", json_schema_extra={"unit": "MPa"}, gt=0)
    fctm_MPa: float = Field(description="Resistenza media a trazione fctm", json_schema_extra={"unit": "MPa"}, gt=0)
    fctk_MPa: float = Field(description="Resistenza caratteristica a trazione fctk (frattile 5%)", json_schema_extra={"unit": "MPa"}, gt=0)
    fcd_MPa: float = Field(description="Resistenza di calcolo a compressione fcd", json_schema_extra={"unit": "MPa"}, gt=0)
    fctd_MPa: float = Field(description="Resistenza di calcolo a trazione fctd", json_schema_extra={"unit": "MPa"}, gt=0)
