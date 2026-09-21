"""Literal type and frozen result models for structural steel grades (EN1993-1-1 §3.2, Tab. 3.1;
acciaio-colonne-ec3!Materiali)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SteelGrade = Literal["S235", "S275", "S355", "S420", "S460"]


class SteelProperties(BaseModel):
    """Mechanical properties of a structural steel grade, at a given nominal thickness."""

    model_config = ConfigDict(frozen=True)

    grado: SteelGrade = Field(description="Grado dell'acciaio da carpenteria")
    t_mm: float = Field(description="Spessore nominale dell'elemento", json_schema_extra={"unit": "mm"}, gt=0)
    fyk_MPa: float = Field(description="Tensione caratteristica di snervamento fyk", json_schema_extra={"unit": "MPa"}, gt=0)
    fuk_MPa: float = Field(description="Tensione caratteristica di rottura fuk", json_schema_extra={"unit": "MPa"}, gt=0)
    e_MPa: float = Field(description="Modulo elastico E", json_schema_extra={"unit": "MPa"}, gt=0)
    g_MPa: float = Field(description="Modulo di elasticità tangenziale G", json_schema_extra={"unit": "MPa"}, gt=0)


class PartialFactors(BaseModel):
    """Coefficienti di sicurezza parziali per l'acciaio strutturale (acciaio-colonne-ec3!Materiali E4:E6)."""

    model_config = ConfigDict(frozen=True)

    gamma_m0: float = Field(description="γM0 — resistenza delle sezioni di classe 1-2-3-4", gt=0)
    gamma_m1: float = Field(description="γM1 — resistenza all'instabilità delle membrature", gt=0)
    gamma_m2: float = Field(description="γM2 — resistenza a rottura delle sezioni tese", gt=0)
