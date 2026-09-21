"""I/O models for `acciaio-proprieta-temperatura` (acciaio-incendio!fuoco-materiali).

Spec: docs/specs/small-units.md §"Tool 1: fuoco-materiali — steel reduction factors at
temperature θ". Thin wrapper over `strutture.shared.fire_reduction`; no reduction table lives
here.
"""
from pydantic import BaseModel, ConfigDict, Field


class ProprietaTemperaturaInput(BaseModel):
    """fuoco-materiali!C20:C22 — one steel grade's nominal properties at 20°C plus a target θ.

    The workbook has four sheets (550/600/650/700 °C); they are the same calculation run at
    different θ, so θ is a free input here rather than four separate tools."""

    model_config = ConfigDict(frozen=True)

    fyk_MPa: float = Field(
        default=355.0,
        description="Tensione di snervamento caratteristica a 20°C",
        json_schema_extra={"unit": "MPa", "symbol": "f_yk", "group": "Materiali"},
        gt=0,
    )
    ea_20_MPa: float = Field(
        default=210000.0,
        description="Modulo elastico di riferimento a 20°C",
        json_schema_extra={"unit": "MPa", "symbol": "E_a", "group": "Materiali"},
        gt=0,
    )
    theta_C: float = Field(
        description="Temperatura dell'acciaio (es. temperatura critica dalla verifica di resistenza al fuoco)",
        json_schema_extra={"unit": "°C", "symbol": "θ", "group": "Parametri di calcolo"},
        ge=20,
        le=1200,
    )
    legacy_compat: bool = Field(
        default=False,
        description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )


class ProprietaTemperaturaOutput(BaseModel):
    """fuoco-materiali!C23:C25 — reduced material properties at θ."""

    model_config = ConfigDict(frozen=True)

    ky_theta: float = Field(description="Fattore di riduzione della tensione di snervamento", ge=0, le=1, json_schema_extra={"unit": "-", "symbol": "k_y,θ"})
    kp_theta: float = Field(description="Fattore di riduzione del limite di proporzionalità", ge=0, le=1, json_schema_extra={"unit": "-", "symbol": "k_p,θ"})
    kE_theta: float = Field(description="Fattore di riduzione del modulo elastico", ge=0, le=1, json_schema_extra={"unit": "-", "symbol": "k_E,θ"})
    fp_theta_MPa: float = Field(description="Limite di proporzionalità ridotto alla temperatura θ (classi 3-4)", ge=0, json_schema_extra={"unit": "MPa", "symbol": "f_p,θ", "highlight": True})
    fy_theta_MPa: float = Field(description="Tensione di snervamento efficace ridotta alla temperatura θ (classi 1-2)", ge=0, json_schema_extra={"unit": "MPa", "symbol": "f_y,θ", "highlight": True})
    ea_theta_MPa: float = Field(description="Modulo elastico ridotto alla temperatura θ", ge=0, json_schema_extra={"unit": "MPa", "symbol": "E_a,θ", "highlight": True})
