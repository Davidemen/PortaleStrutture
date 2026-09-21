"""Result models for the strut-and-tie verification of the pile cap (see `puntoni_tiranti.py`)."""
from pydantic import BaseModel, ConfigDict, Field


class Puntone(BaseModel):
    """Main diagonal compression strut, from the governing pile to the column node (EC2 §6.5.2/§6.5.4).
    `theta_deg` is `None` for a single-pile cap (direct bearing, no strut-and-tie mechanism)."""

    model_config = ConfigDict(frozen=True)

    lxy_m: float = Field(description="Distanza in pianta dal centro del gruppo pali al palo", ge=0, json_schema_extra={"unit": "m", "symbol": "L_XY"})
    h_wt2_m: float = Field(description="Braccio verticale, altezza plinto meno metà spessore tirante", json_schema_extra={"unit": "m", "symbol": "h-w_t/2"})
    theta_deg: float | None = Field(description="Inclinazione del puntone (None = appoggio diretto, schema 1x1)",
                                     json_schema_extra={"unit": "°", "symbol": "θ"})
    wt_mm: float = Field(description="Spessore del tirante superiore (0 = appoggio diretto, schema 1x1)",
                          ge=0, json_schema_extra={"unit": "mm", "symbol": "w_t"})
    ws_mm: float | None = Field(description="Larghezza del puntone proiettata sul nodo", json_schema_extra={"unit": "mm", "symbol": "w_s"})
    acs_mm2: float = Field(description="Area della sezione trasversale del puntone/nodo", gt=0, json_schema_extra={"unit": "mm2"})
    fus_kN: float = Field(description="Forza di compressione nel puntone", ge=0, json_schema_extra={"unit": "kN", "symbol": "F_us"})
    sigma_rd_max_MPa: float = Field(description="Tensione di compressione massima ammissibile nel nodo", gt=0, json_schema_extra={"unit": "N/mm2"})
    fns_kN: float = Field(description="Resistenza di progetto del puntone", ge=0, json_schema_extra={"unit": "kN", "symbol": "F_ns"})
    verificato: bool = Field(description="Fns > Fus")
    utilizzo: float = Field(description="Fus / Fns", ge=0, json_schema_extra={"unit": "-"})


class Tirante(BaseModel):
    """One tie resisting the strut's horizontal component (EC2 §6.5.3/§9.8.1, rebar-as-tie)."""

    model_config = ConfigDict(frozen=True)

    fut_kN: float = Field(description="Forza di trazione richiesta nel tirante", ge=0, json_schema_extra={"unit": "kN", "symbol": "F_ut"})
    diametro_mm: float = Field(description="Diametro delle barre del tirante", gt=0, json_schema_extra={"unit": "mm"})
    n_barre: int = Field(description="Numero di barre del tirante", ge=1, json_schema_extra={"unit": "-"})
    at_mm2: float = Field(description="Area di armatura del tirante", gt=0, json_schema_extra={"unit": "mm2"})
    fnt_kN: float = Field(description="Resistenza di progetto del tirante", gt=0, json_schema_extra={"unit": "kN", "symbol": "F_nt"})
    verificato: bool = Field(description="Fnt > Fut")
    utilizzo: float = Field(description="Fut / Fnt", ge=0, json_schema_extra={"unit": "-"})


class PuntoniTiranti(BaseModel):
    """Strut-and-tie verification of the governing (Nmax) pile cap section. Tie fields are `None`
    where the pile pattern has no tie in that direction (single-pile cap: none at all)."""

    model_config = ConfigDict(frozen=True)

    puntone: Puntone = Field(description="Verifica del puntone diagonale principale")
    tirante_xy: Tirante | None = Field(description="Tirante diagonale XY (solo schema 2x2)")
    tirante_x: Tirante | None = Field(description="Tirante lungo X")
    tirante_y: Tirante | None = Field(description="Tirante lungo Y")
