"""Shared geometry / seismic parameters results of the `muro-sostegno` tool (split out of
`models.py`, regola dura 12 dei moduli piccoli): common to all 8 combinations.
"""
from pydantic import BaseModel, ConfigDict, Field


class GeometriaResult(BaseModel):
    """Muro!I30, I33:I35, I11:I12, I39."""

    model_config = ConfigDict(frozen=True)

    h_muro_tot_m: float = Field(description="Altezza totale del muro (fusto + fondazione)", gt=0, json_schema_extra={"unit": "m", "symbol": "H"})
    b_fond_m: float = Field(description="Larghezza totale della fondazione", gt=0, json_schema_extra={"unit": "m", "symbol": "B"})
    a_muro_m2: float = Field(description="Area della sezione trasversale del muro (fusto + fondazione)", gt=0, json_schema_extra={"unit": "m2"})
    x_muro_m: float = Field(description="Baricentro del muro dal polo di ribaltamento (punta valle)", gt=0, json_schema_extra={"unit": "m"})
    z_muro_m: float = Field(description="Baricentro del muro dalla base della fondazione (braccio verticale per l'inerzia sismica)", gt=0, json_schema_extra={"unit": "m"})
    a_terr_m2: float = Field(description="Area della sezione trasversale del cuneo di terreno a tergo", ge=0, json_schema_extra={"unit": "m2"})
    x_terr_m: float = Field(description="Baricentro del terreno dal polo di ribaltamento", gt=0, json_schema_extra={"unit": "m"})
    z_terr_m: float = Field(description="Baricentro del cuneo di terreno dalla base della fondazione (braccio verticale per l'inerzia sismica)", gt=0, json_schema_extra={"unit": "m"})
    x_sv_m: float = Field(description="Baricentro del sovraccarico dal polo di ribaltamento", gt=0, json_schema_extra={"unit": "m"})


class ParametriSismiciResult(BaseModel):
    """Muro!I18:I20 (Ss/ST/S, sempre calcolati dalla categoria di sottosuolo/topografica)."""

    model_config = ConfigDict(frozen=True)

    ss: float = Field(description="Coefficiente di amplificazione stratigrafica", gt=0, json_schema_extra={"unit": "-", "symbol": "S_S"})
    st: float = Field(description="Coefficiente di amplificazione topografica", gt=0, json_schema_extra={"unit": "-", "symbol": "S_T"})
    s: float = Field(description="Coefficiente che tiene conto della categoria di sottosuolo, S = Ss·ST", gt=0, json_schema_extra={"unit": "-", "symbol": "S"})
