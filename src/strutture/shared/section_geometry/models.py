"""Frozen result models for elastic section-geometry properties, shared by CA member tools."""
from pydantic import BaseModel, ConfigDict, Field


class SectionProperties(BaseModel):
    """Elastic properties of a full (uncracked) cross-section."""

    model_config = ConfigDict(frozen=True)

    area_mm2: float = Field(description="Area della sezione A", json_schema_extra={"unit": "mm2"}, gt=0)
    inertia_mm4: float = Field(description="Momento d'inerzia I", json_schema_extra={"unit": "mm4"}, gt=0)
    radius_of_gyration_mm: float = Field(description="Raggio d'inerzia i = sqrt(I/A)",
                                          json_schema_extra={"unit": "mm"}, gt=0)
    section_modulus_mm3: float = Field(description="Modulo di resistenza elastico W = I/y_max",
                                        json_schema_extra={"unit": "mm3"}, gt=0)


class CrackedSectionResult(BaseModel):
    """Cracked (stage-II) elastic properties of a rectangular RC section, n=15 homogenisation."""

    model_config = ConfigDict(frozen=True)

    x_mm: float = Field(description="Profondità dell'asse neutro x dal lembo compresso",
                         json_schema_extra={"unit": "mm"}, gt=0)
    inertia_cracked_mm4: float = Field(description="Momento d'inerzia della sezione parzializzata Ii",
                                        json_schema_extra={"unit": "mm4"}, gt=0)
