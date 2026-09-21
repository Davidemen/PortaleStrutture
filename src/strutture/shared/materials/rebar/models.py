"""Literal type and frozen result model for the rebar grade roster (NTC2018 §11.3.2; merge C1 in
docs/architecture.md §3 — union of ca-travi/ca-mensole/ca-pilastri!Tabelle M44:P50)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RebarGrade = Literal[
    "B450C", "B450A", "B500C", "FeB22k", "FeB32k", "FeB38k", "FeB44k", "RB500W",
]


class RebarProperties(BaseModel):
    """Mechanical properties of a rebar grade."""

    model_config = ConfigDict(frozen=True)

    grado: RebarGrade = Field(description="Grado (marchio) dell'acciaio da armatura")
    fyk_MPa: float = Field(description="Tensione caratteristica di snervamento fyk", json_schema_extra={"unit": "MPa"}, gt=0)
    ftk_MPa: float = Field(description="Tensione caratteristica di rottura ftk", json_schema_extra={"unit": "MPa"}, gt=0)
    fyd_MPa: float = Field(description="Tensione di calcolo di snervamento fyd = fyk/γs", json_schema_extra={"unit": "MPa"}, gt=0)
    es_MPa: float = Field(description="Modulo elastico dell'acciaio Es", json_schema_extra={"unit": "MPa"}, gt=0)
    sigma_amm_MPa: float | None = Field(
        default=None,
        description="Tensione ammissibile σamm (metodo delle tensioni ammissibili, solo per riferimento storico)",
        json_schema_extra={"unit": "MPa"},
    )
    legacy_grade: bool = Field(
        description="True se il grado non è tra quelli ammessi da NTC §11.3.2 (B450C/B450A) per nuove opere",
    )
