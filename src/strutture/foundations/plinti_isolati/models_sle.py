"""Result model for the SLS concrete/steel stress checks (see `sle.py`)."""
from pydantic import BaseModel, ConfigDict, Field


class Sle(BaseModel):
    """Concrete/steel elastic stresses under the quasi-permanent/characteristic/frequent envelopes."""

    model_config = ConfigDict(frozen=True)

    sigma_c_qp_MPa: float | None = Field(description="Tensione nel calcestruzzo, combinazione quasi permanente (None se la famiglia SLE_QP non è in tabella)", ge=0, json_schema_extra={"unit": "N/mm2"})
    sigma_s_qp_MPa: float | None = Field(description="Tensione nell'acciaio, combinazione quasi permanente (None se la famiglia SLE_QP non è in tabella)", ge=0, json_schema_extra={"unit": "N/mm2"})
    sigma_c_rara_MPa: float | None = Field(description="Tensione nel calcestruzzo, combinazione caratteristica (rara) (None se la famiglia SLE_RARA non è in tabella)", ge=0, json_schema_extra={"unit": "N/mm2"})
    sigma_s_rara_MPa: float | None = Field(description="Tensione nell'acciaio, combinazione caratteristica (rara) (None se la famiglia SLE_RARA non è in tabella)", ge=0, json_schema_extra={"unit": "N/mm2"})
    sigma_s_freq_MPa: float | None = Field(description="Tensione nell'acciaio, combinazione frequente (None se la famiglia SLE_FREQ non è in tabella)", ge=0, json_schema_extra={"unit": "N/mm2"})
