"""Literal types and frozen result models for the NTC 2018 §6.2/§6.5 partial-factor combinations."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ApproccioAzioni = Literal["EQU", "A1", "A2"]  # NTC2018 Tab. 6.2.I — approcci per le azioni
ApproccioGeotecnico = Literal["M1", "M2"]  # NTC2018 Tab. 6.2.II — approcci per i parametri geotecnici
ApproccioResistenza = Literal["R1", "R2", "R3"]  # NTC2018 Tab. 6.5.I — approcci per la resistenza
VerificaOpereDiSostegno = Literal[
    "capacita_portante", "scorrimento", "resistenza_terreno_a_valle", "ribaltamento"
]


class FattoriAzioni(BaseModel):
    """NTC2018 Tab. 6.2.I — coefficienti parziali per le azioni (o l'effetto delle azioni)."""

    model_config = ConfigDict(frozen=True)

    gamma_g1_favorevole: float = Field(description="Carichi permanenti G1, favorevoli", gt=0, json_schema_extra={"unit": "-"})
    gamma_g1_sfavorevole: float = Field(description="Carichi permanenti G1, sfavorevoli", gt=0, json_schema_extra={"unit": "-"})
    gamma_g2_favorevole: float = Field(description="Carichi permanenti non strutturali G2, favorevoli", ge=0, json_schema_extra={"unit": "-"})
    gamma_g2_sfavorevole: float = Field(description="Carichi permanenti non strutturali G2, sfavorevoli", ge=0, json_schema_extra={"unit": "-"})
    gamma_q_favorevole: float = Field(description="Carichi variabili Q, favorevoli", ge=0, json_schema_extra={"unit": "-"})
    gamma_q_sfavorevole: float = Field(description="Carichi variabili Q, sfavorevoli", ge=0, json_schema_extra={"unit": "-"})


class FattoriGeotecnici(BaseModel):
    """NTC2018 Tab. 6.2.II — coefficienti parziali per i parametri geotecnici."""

    model_config = ConfigDict(frozen=True)

    gamma_tan_phi: float = Field(description="Tangente dell'angolo di resistenza al taglio tan φ'k", gt=0, json_schema_extra={"unit": "-"})
    gamma_c: float = Field(description="Coesione efficace c'k", gt=0, json_schema_extra={"unit": "-"})
    gamma_cu: float = Field(description="Resistenza non drenata cuk", gt=0, json_schema_extra={"unit": "-"})
    gamma_gamma: float = Field(description="Peso dell'unità di volume γ", gt=0, json_schema_extra={"unit": "-"})


class FattoriResistenza(BaseModel):
    """NTC2018 Tab. 6.5.I — coefficienti parziali γR per le verifiche di sicurezza delle opere di sostegno."""

    model_config = ConfigDict(frozen=True)

    r1: float = Field(description="Coefficiente parziale γR, approccio R1", gt=0, json_schema_extra={"unit": "-"})
    r2: float = Field(description="Coefficiente parziale γR, approccio R2", gt=0, json_schema_extra={"unit": "-"})
    r3: float = Field(description="Coefficiente parziale γR, approccio R3", gt=0, json_schema_extra={"unit": "-"})
