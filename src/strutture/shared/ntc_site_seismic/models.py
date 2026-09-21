"""Literal types and frozen result models for the NTC 2018 hazard/site chain (§2.4.3, §3.2)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ClasseUso = Literal["I", "II", "III", "IV"]
StatoLimite = Literal["SLO", "SLD", "SLV", "SLC"]
CategoriaSottosuolo = Literal["A", "B", "C", "D", "E"]  # NTC2018 Tab. 3.2.II — categorie di sottosuolo
CategoriaTopografica = Literal["T1", "T2", "T3", "T4"]  # NTC2018 Tab. 3.2.III — categorie topografiche


class VitaRiferimentoResult(BaseModel):
    """Sisma!I9:I10 — coefficiente d'uso and vita di riferimento."""

    model_config = ConfigDict(frozen=True)

    cu: float = Field(description="Coefficiente d'uso Cu", json_schema_extra={"unit": "-"}, gt=0)
    vr: float = Field(description="Vita di riferimento VR", json_schema_extra={"unit": "anni"}, gt=0)


class PeriodiRitornoResult(BaseModel):
    """Sisma!D13:D16 — periodo di ritorno TR per ciascuno dei 4 stati limite."""

    model_config = ConfigDict(frozen=True)

    slo: float = Field(description="Periodo di ritorno TR, stato limite SLO", json_schema_extra={"unit": "anni"}, gt=0)
    sld: float = Field(description="Periodo di ritorno TR, stato limite SLD", json_schema_extra={"unit": "anni"}, gt=0)
    slv: float = Field(description="Periodo di ritorno TR, stato limite SLV", json_schema_extra={"unit": "anni"}, gt=0)
    slc: float = Field(description="Periodo di ritorno TR, stato limite SLC", json_schema_extra={"unit": "anni"}, gt=0)


class AmplificazioneResult(BaseModel):
    """Sisma!I31:I34 — coefficienti di amplificazione stratigrafica/topografica."""

    model_config = ConfigDict(frozen=True)

    ss: float = Field(description="Coefficiente di amplificazione stratigrafica Ss", json_schema_extra={"unit": "-"}, gt=0)
    cc: float = Field(description="Coefficiente di correzione del periodo Cc", json_schema_extra={"unit": "-"}, gt=0)
    st: float = Field(description="Coefficiente di amplificazione topografica ST", json_schema_extra={"unit": "-"}, gt=0)
    s: float = Field(description="Coefficiente di amplificazione del suolo S = Ss·ST", json_schema_extra={"unit": "-"}, gt=0)


class PeriodiSpettroResult(BaseModel):
    """Sisma!I48:I50 — periodi caratteristici dello spettro di risposta."""

    model_config = ConfigDict(frozen=True)

    tb: float = Field(description="Periodo TB (inizio tratto ad accelerazione costante)", json_schema_extra={"unit": "s"}, gt=0)
    tc: float = Field(description="Periodo TC (inizio tratto a velocità costante)", json_schema_extra={"unit": "s"}, gt=0)
    td: float = Field(description="Periodo TD (inizio tratto a spostamento costante)", json_schema_extra={"unit": "s"}, gt=0)
