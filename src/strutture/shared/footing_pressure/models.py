"""Frozen result models for rigid rectangular footing contact pressure.

SI-engineering units throughout (kN, m, kPa) — see docs/architecture-batch2.md §9-D1: the
SI/tecnico unit boundary belongs to the calling Tool, not to this shared physics module.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Metodo = Literal["esatto", "sovrapposizione"]


class NeutralAxis(BaseModel):
    """Zero-pressure line of a no-tension plane-pressure solution.

    sigma(x, y) = k_kpa_m * (n . (x, y) - offset_m) on the compressed side, 0 beyond it, where
    n = (cos(theta_rad), sin(theta_rad)) is the unit vector (from the footing centroid) pointing
    towards increasing pressure.
    """

    model_config = ConfigDict(frozen=True)

    theta_rad: float = Field(description="Direzione del gradiente di pressione dal baricentro del plinto",
                              json_schema_extra={"unit": "rad"})
    offset_m: float = Field(description="Distanza con segno, lungo theta, del punto a pressione nulla dal baricentro",
                             json_schema_extra={"unit": "m"})
    k_kpa_m: float = Field(description="Gradiente di pressione lungo theta", json_schema_extra={"unit": "kPa/m"},
                            gt=0)


class UniaxialPressure(BaseModel):
    """Contact pressure of a rigid footing under uniaxial bending (N and M about one axis only)."""

    model_config = ConfigDict(frozen=True)

    e_m: float = Field(description="Eccentricità e = M/N", json_schema_extra={"unit": "m"})
    in_kern: bool = Field(description="True se l'eccentricità è entro il nocciolo d'inerzia (|e| <= l/6)")
    sigma_max_kpa: float = Field(description="Pressione di contatto massima", json_schema_extra={"unit": "kPa"},
                                  ge=0)
    sigma_min_kpa: float = Field(description="Pressione di contatto minima (0 se parzializzata)",
                                  json_schema_extra={"unit": "kPa"}, ge=0)
    contact_len_m: float = Field(description="Lunghezza reagente lungo l (l se non parzializzata)",
                                  json_schema_extra={"unit": "m"}, gt=0)


class BiaxialPressure(BaseModel):
    """Contact pressure of a rigid rectangular footing (bx * by) under biaxial bending N, Mx, My."""

    model_config = ConfigDict(frozen=True)

    metodo: Metodo = Field(description="Metodo di calcolo utilizzato")
    ex_m: float = Field(description="Eccentricità lungo X, ex = My/N", json_schema_extra={"unit": "m"})
    ey_m: float = Field(description="Eccentricità lungo Y, ey = Mx/N", json_schema_extra={"unit": "m"})
    in_kern: bool = Field(description="True se (ex,ey) è entro il nocciolo d'inerzia biassiale (rombo)")
    sigma_max_kpa: float = Field(description="Pressione di contatto massima", json_schema_extra={"unit": "kPa"},
                                  ge=0)
    sigma_min_kpa: float = Field(description="Pressione di contatto minima (0 se parzializzata)",
                                  json_schema_extra={"unit": "kPa"}, ge=0)
    compressed_ratio: float = Field(description="Rapporto fra base reagente e base totale del plinto (1 = tutta "
                                     "compressa)", ge=0, le=1)
    corners_kpa: tuple[float, float, float, float] = Field(
        description="Pressione ai 4 vertici del plinto, ordine (-x,-y) (+x,-y) (+x,+y) (-x,+y)",
        json_schema_extra={"unit": "kPa"})
    neutral_axis: NeutralAxis | None = Field(
        default=None, description="Asse neutro della soluzione a contatto parziale (solo metodo esatto fuori "
        "nocciolo, altrimenti None)")
    warning: str | None = Field(default=None, description="Avviso del metodo di calcolo, se applicabile")
