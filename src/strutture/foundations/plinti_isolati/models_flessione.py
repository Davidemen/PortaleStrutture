"""Result model for the flexural reinforcement design step (see `flessione.py`)."""
from pydantic import BaseModel, ConfigDict, Field


class Flessione(BaseModel):
    """Bending moment at the column face + required/provided flexural reinforcement, both directions."""

    model_config = ConfigDict(frozen=True)

    mx_slu_kNm: float = Field(description="Momento flettente di progetto Mx,SLU (direzione X)", ge=0, json_schema_extra={"unit": "kNm"})
    my_slu_kNm: float = Field(description="Momento flettente di progetto My,SLU (direzione Y)", ge=0, json_schema_extra={"unit": "kNm"})
    as_x_cm2: float = Field(description="Armatura richiesta in direzione X", ge=0, json_schema_extra={"unit": "cm2"})
    as_y_cm2: float = Field(description="Armatura richiesta in direzione Y", ge=0, json_schema_extra={"unit": "cm2"})
    as_x_min_cm2: float = Field(description="Armatura minima in direzione X", ge=0, json_schema_extra={"unit": "cm2"})
    as_y_min_cm2: float = Field(description="Armatura minima in direzione Y", ge=0, json_schema_extra={"unit": "cm2"})
    n_x: int = Field(description="Numero di barre in direzione X", ge=1, json_schema_extra={"unit": "-"})
    n_y: int = Field(description="Numero di barre in direzione Y", ge=1, json_schema_extra={"unit": "-"})
    phi_x_mm: float = Field(description="Diametro barre in direzione X", gt=0, json_schema_extra={"unit": "mm"})
    phi_y_mm: float = Field(description="Diametro barre in direzione Y", gt=0, json_schema_extra={"unit": "mm"})
    phi_min_mm: float = Field(description="Diametro minimo per il controllo fessurativo", gt=0, json_schema_extra={"unit": "mm"})
    as_prov_x_mm2: float = Field(description="Armatura effettivamente disposta in direzione X", gt=0, json_schema_extra={"unit": "mm2"})
    as_prov_y_mm2: float = Field(description="Armatura effettivamente disposta in direzione Y", gt=0, json_schema_extra={"unit": "mm2"})
    callout_sup_x: str = Field(description="Disposizione armatura superiore, direzione X")
    callout_inf_x: str = Field(description="Disposizione armatura inferiore, direzione X")
    callout_sup_y: str = Field(description="Disposizione armatura superiore, direzione Y")
    callout_inf_y: str = Field(description="Disposizione armatura inferiore, direzione Y")
