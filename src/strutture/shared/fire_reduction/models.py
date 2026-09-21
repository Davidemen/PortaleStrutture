"""Frozen result model for EN1993-1-2 Table 3.1 reduction factors at a given steel temperature."""
from pydantic import BaseModel, ConfigDict, Field


class ReductionFactors(BaseModel):
    """ky,θ / kp,θ / kE,θ — EN1993-1-2 Tab. 3.1, interpolated at one temperature θ."""

    model_config = ConfigDict(frozen=True)

    theta_C: float = Field(description="Temperatura dell'acciaio θ", json_schema_extra={"unit": "°C"})
    ky_theta: float = Field(description="Fattore di riduzione della tensione di snervamento ky,θ", ge=0, le=1)
    kp_theta: float = Field(description="Fattore di riduzione del limite di proporzionalità kp,θ", ge=0, le=1)
    kE_theta: float = Field(description="Fattore di riduzione del modulo elastico kE,θ", ge=0, le=1)
