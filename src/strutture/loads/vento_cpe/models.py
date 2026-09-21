"""Pydantic I/O models for the vento-cpe-rettangolare tool (Circ. NTC2019 §C3.3.8.1)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.sketch import Sketch, campo_schizzo


class VentoCpeInput(BaseModel):
    """Plan geometry of a rectangular-plan building."""

    model_config = ConfigDict(frozen=True)

    b: float = Field(
        description="Larghezza in pianta, vento perpendicolare al lato b", gt=0,
        json_schema_extra={"unit": "m", "symbol": "b", "group": "Geometria in pianta"},
    )
    d: float = Field(
        description="Profondità in pianta", gt=0,
        json_schema_extra={"unit": "m", "symbol": "d", "group": "Geometria in pianta"},
    )
    h: float = Field(
        description="Altezza dell'edificio", gt=0,
        json_schema_extra={"unit": "m", "symbol": "h", "group": "Geometria in pianta"},
    )
    legacy_compat: bool = Field(
        default=False,
        description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )


class DirectionResult(BaseModel):
    """cpe results for one wind direction."""

    model_config = ConfigDict(frozen=True)

    h_d: float = Field(description="Rapporto tra altezza e profondità", json_schema_extra={"unit": "-", "symbol": "h/d"})
    cpe_windward: float | None = Field(
        default=None,
        description="Coefficiente di pressione esterna sulla parete sopravento (non definito per h/d > 5)",
        json_schema_extra={"unit": "-", "symbol": "c_pe,sopravento"},
    )
    cpe_side: float | None = Field(
        default=None,
        description="Coefficiente di pressione esterna sulle pareti laterali (non definito per h/d > 5)",
        json_schema_extra={"unit": "-", "symbol": "c_pe,laterale"},
    )
    cpe_leeward: float | None = Field(
        default=None,
        description="Coefficiente di pressione esterna sulla parete sottovento (non definito per h/d > 5)",
        json_schema_extra={"unit": "-", "symbol": "c_pe,sottovento"},
    )


class VentoCpeOutput(BaseModel):
    """cpe results for both wind directions plus overall classification."""

    model_config = ConfigDict(frozen=True)

    classification: str = Field(
        description="Classificazione di snellezza dell'edificio",
        json_schema_extra={"unit": "-", "highlight": True},
    )
    dir1: DirectionResult = Field(description="Direzione 1 — vento perpendicolare al lato b")
    dir2: DirectionResult = Field(description="Direzione 2 — vento perpendicolare al lato d")
    schizzo: Sketch | None = campo_schizzo()
