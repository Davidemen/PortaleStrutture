"""Result models for the bottom ("inf") and top ("sup") flexural design of the pile cap slab
(see `flessione.py`)."""
from pydantic import BaseModel, ConfigDict, Field


class DesignFlessione(BaseModel):
    """One direction's flexural design, as a 1-meter-wide slab strip (docs/specs/fond-plinti-pali.md
    Tool-2, `Footing check!AU-BA`: every quantity here is already `mm²/m`)."""

    model_config = ConfigDict(frozen=True)

    mu_kNm: float = Field(description="Momento flettente di progetto Mu", ge=0, json_schema_extra={"unit": "kNm"})
    as_min_mm2: float = Field(description="Armatura minima", ge=0, json_schema_extra={"unit": "mm2/m"})
    as_req_flexural_mm2: float = Field(description="Armatura richiesta a flessione", ge=0, json_schema_extra={"unit": "mm2/m"})
    as_req_mm2: float = Field(description="Armatura richiesta, MAX(flessione, minima)", ge=0, json_schema_extra={"unit": "mm2/m"})
    diametro_mm: float = Field(description="Diametro delle barre", gt=0, json_schema_extra={"unit": "mm"})
    passo_mm: float = Field(description="Passo delle barre", gt=0, json_schema_extra={"unit": "mm"})
    n_barre_per_m: int = Field(description="Numero di barre per metro", ge=1, json_schema_extra={"unit": "-"})
    as_prov_mm2: float = Field(description="Armatura effettivamente disposta", gt=0, json_schema_extra={"unit": "mm2/m"})
    verificato: bool = Field(description="As disposta >= As richiesta")


class Flessione(BaseModel):
    """Bottom + top flexural design of the pile cap slab, both directions (docs/specs/fond-plinti-pali.md
    Tool-2; top reinforcement is a simplified secondary check, not surfaced in `Per Relazione`)."""

    model_config = ConfigDict(frozen=True)

    inf_x: DesignFlessione = Field(description="Armatura inferiore, direzione X-X")
    inf_y: DesignFlessione = Field(description="Armatura inferiore, direzione Y-Y")
    sup_x: DesignFlessione = Field(description="Armatura superiore, direzione X-X (verifica semplificata)")
    sup_y: DesignFlessione = Field(description="Armatura superiore, direzione Y-Y (verifica semplificata)")
