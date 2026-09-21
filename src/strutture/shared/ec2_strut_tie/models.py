"""Frozen result models for EN 1992-1-1 §6.5 strut-and-tie calculations."""
from pydantic import BaseModel, ConfigDict, Field


class NodeResistance(BaseModel):
    """Design compressive stress limit at a strut-and-tie node (§6.5.4)."""

    model_config = ConfigDict(frozen=True)

    sigma_rd_max_MPa: float = Field(description="Tensione di compressione massima ammissibile nel nodo", ge=0)
    nu_prime: float = Field(description="Coefficiente di riduzione ν' = 1 - fck/250", ge=0)
    fcd_MPa: float = Field(description="Resistenza di calcolo a compressione del calcestruzzo fcd", ge=0)


class StrutResistance(BaseModel):
    """Design compressive stress limit (and, when a cross-section is given, force) of a concrete strut (§6.5.2)."""

    model_config = ConfigDict(frozen=True)

    sigma_rd_max_MPa: float = Field(description="Tensione di compressione massima ammissibile nel puntone", ge=0)
    nu_prime: float = Field(description="Coefficiente di riduzione ν' = 1 - fck/250", ge=0)
    fcd_MPa: float = Field(description="Resistenza di calcolo a compressione del calcestruzzo fcd", ge=0)
    cracked: bool = Field(description="Stato fessurativo assunto per il puntone (True = fessurato, ridotto)")
    fns_kN: float | None = Field(
        description="Resistenza di calcolo del puntone come forza, quando è nota la sezione trasversale", ge=0
    )
