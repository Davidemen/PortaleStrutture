"""I/O models for `acciaio-resistenza-incendio` (acciaio-incendio!resistenza)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GradoAcciaioIncendio = Literal["S235", "S275", "S355"]

DEFAULT_TEMPI_MIN: tuple[float, ...] = tuple(float(t) for t in range(5, 121, 5))


class ResistenzaIncendioInput(BaseModel):
    """resistenza!D2:D3 + B9:B32 fill-down."""

    model_config = ConfigDict(frozen=True)

    grado: GradoAcciaioIncendio = Field(description="Grado dell'acciaio da carpenteria", json_schema_extra={"unit": "-", "group": "Materiali"})
    e_20_MPa: float = Field(
        default=210000.0, description="Modulo elastico di riferimento a 20°C", json_schema_extra={"unit": "MPa", "symbol": "E", "group": "Materiali"}, gt=0,
    )
    tempi_min: tuple[float, ...] = Field(
        default=DEFAULT_TEMPI_MIN,
        description="Durate di esposizione all'incendio da valutare",
        json_schema_extra={"unit": "min", "symbol": "t", "group": "Parametri di calcolo"},
        min_length=1,
    )
    legacy_compat: bool = Field(default=False, description="Riproduci il foglio Excel originale (errori inclusi)", json_schema_extra={"group": "Avanzate", "advanced": True})


class MaterialeBase(BaseModel):
    """resistenza!D4:D5 — proprietà nominali a 20°C."""

    model_config = ConfigDict(frozen=True)

    fy_20_MPa: float = Field(description="Tensione di snervamento nominale a 20°C", json_schema_extra={"unit": "MPa", "symbol": "f_y,20°C"}, gt=0)
    fu_20_MPa: float = Field(description="Tensione di rottura nominale a 20°C", json_schema_extra={"unit": "MPa", "symbol": "f_u,20°C"}, gt=0)


class RigaResistenzaIncendio(BaseModel):
    """One row of resistenza!B9:H32, indexed by exposure time t."""

    model_config = ConfigDict(frozen=True)

    t_min: float = Field(description="Durata di esposizione all'incendio", json_schema_extra={"unit": "min", "symbol": "t"}, ge=0)
    theta_C: float = Field(description="Temperatura del gas/acciaio (curva ISO 834)", json_schema_extra={"unit": "°C", "symbol": "θ"})
    ky_theta: float = Field(description="Fattore di riduzione della tensione di snervamento", ge=0, le=1, json_schema_extra={"unit": "-", "symbol": "k_y,θ"})
    kE_theta: float = Field(description="Fattore di riduzione del modulo elastico", ge=0, le=1, json_schema_extra={"unit": "-", "symbol": "k_E,θ"})
    fy_theta_MPa: float = Field(description="Tensione di snervamento ridotta alla temperatura θ", json_schema_extra={"unit": "MPa", "symbol": "f_y,θ"}, ge=0)
    fu_theta_MPa: float = Field(description="Tensione di rottura ridotta alla temperatura θ", json_schema_extra={"unit": "MPa", "symbol": "f_u,θ"}, ge=0)
    e_theta_MPa: float = Field(description="Modulo elastico ridotto alla temperatura θ", json_schema_extra={"unit": "MPa", "symbol": "E_θ"}, ge=0)


class ResistenzaIncendioOutput(BaseModel):
    """resistenza!D4:D5 + B9:H32."""

    model_config = ConfigDict(frozen=True)

    materiale: MaterialeBase
    righe: tuple[RigaResistenzaIncendio, ...] = Field(
        description="Tensioni e modulo elastico ridotti per ciascuna durata di esposizione",
        json_schema_extra={
            "chart": {
                "x": "t_min", "y": ["fy_theta_MPa", "fu_theta_MPa"],
                "x_label": "Durata di esposizione t [min]", "y_label": "Tensione [MPa]",
            },
        },
    )
