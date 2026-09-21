"""Pydantic I/O for `geo-cedimento-elastico-timoshenko-goodier`. Inputs flat, ordered as in
`Elastico_Timoshenko_Goodier_3` top to bottom (`docs/specs/geo-cedimenti-elastico.md` Tool 2)."""
from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.sketch import Sketch, campo_schizzo
from strutture.shared.soil_layers import SoilLayer, strati_table_field

from .boundary import SistemaUnita
from .strati_contiguity import validate_ground_strati

_LUNGHEZZA_OPTIONS = {"SI": "m", "tecnico": "cm"}
_PRESSIONE_OPTIONS = {"SI": "kPa", "tecnico": "kg/cm2"}


class TimoshenkoGoodierInput(BaseModel):
    model_config = ConfigDict(frozen=True, json_schema_extra={"unit_selector": "sistema_unita"})

    sistema_unita: SistemaUnita = Field(default="SI", description="Sistema di unità di misura degli input dimensionali", json_schema_extra={"group": "Modalità"})
    b: float = Field(gt=0, description="Larghezza della fondazione", json_schema_extra={"symbol": "B", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria"})
    l: float = Field(gt=0, description="Lunghezza della fondazione", json_schema_extra={"symbol": "L", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria"})
    d: float = Field(ge=0, description="Profondità del piano di posa dal piano di campagna", json_schema_extra={"symbol": "D", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria"})
    mu: float = Field(gt=0, lt=0.5, description="Coefficiente di Poisson del terreno", json_schema_extra={"symbol": "μ", "unit": "-", "group": "Terreno"})
    q: float = Field(gt=0, description="Pressione di contatto uniforme in fondazione", json_schema_extra={"symbol": "q", "unit_options": _PRESSIONE_OPTIONS, "group": "Carico"})
    h_significativo: float | None = Field(
        default=None, gt=0, description="Profondità significativa H (vuoto = 5·B, valore di default del foglio)",
        json_schema_extra={"symbol": "H", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria", "advanced": True},
    )
    strati: tuple[SoilLayer, ...] = strati_table_field(description="Stratigrafia del terreno, dal piano di campagna, fino ad almeno H")
    if_centro: float = Field(gt=0, description="Fattore di forma/profondità IF al centro, letto dal grafico (Fig. 3)", json_schema_extra={"symbol": "IF", "unit": "-", "group": "Fattori dal grafico"})
    if_bordo: float = Field(gt=0, description="Fattore di forma/profondità IF al bordo, letto dal grafico (Fig. 3)", json_schema_extra={"symbol": "IF", "unit": "-", "group": "Fattori dal grafico"})
    legacy_compat: bool = Field(default=False, description="Riproduci il foglio Excel originale (errori inclusi)", json_schema_extra={"group": "Avanzate", "advanced": True})

    @model_validator(mode="after")
    def _stratigrafia_contigua(self) -> "TimoshenkoGoodierInput":
        validate_ground_strati(self.strati)
        return self


class GeometriaTG(BaseModel):
    model_config = ConfigDict(frozen=True)

    a: float = Field(description="Rapporto di forma L/B", json_schema_extra={"symbol": "a", "unit": "-"})
    b_centro: float = Field(description="Rapporto di profondità 2H/B (centro)", json_schema_extra={"symbol": "b_centro", "unit": "-"})
    b_bordo: float = Field(description="Rapporto di profondità H/B (bordo)", json_schema_extra={"symbol": "b_bordo", "unit": "-"})


class ModuloTG(BaseModel):
    model_config = ConfigDict(frozen=True)

    es_MPa: float = Field(description="Modulo elastico medio pesato sullo spessore, su [0,H]", json_schema_extra={"symbol": "Es", "unit": "MPa"})


class FattoriTG(BaseModel):
    model_config = ConfigDict(frozen=True)

    is_centro: float = Field(description="Fattore di influenza allo spostamento IS al centro", json_schema_extra={"symbol": "IS_centro", "unit": "-"})
    is_bordo: float = Field(description="Fattore di influenza allo spostamento IS al bordo", json_schema_extra={"symbol": "IS_bordo", "unit": "-"})
    if_centro: float = Field(description="Fattore di forma/profondità IF al centro (input)", json_schema_extra={"symbol": "IF_centro", "unit": "-"})
    if_bordo: float = Field(description="Fattore di forma/profondità IF al bordo (input)", json_schema_extra={"symbol": "IF_bordo", "unit": "-"})


class CedimentoTG(BaseModel):
    model_config = ConfigDict(frozen=True)

    delta_h_centro_mm: float = Field(description="Cedimento immediato al centro fondazione", json_schema_extra={"unit": "mm", "symbol": "ΔH_centro", "highlight": True})
    delta_h_bordo_mm: float = Field(description="Cedimento immediato al bordo (punto medio) fondazione", json_schema_extra={"unit": "mm", "symbol": "ΔH_bordo", "highlight": True})


class TimoshenkoGoodierOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    geometria: GeometriaTG
    modulo: ModuloTG
    fattori: FattoriTG
    cedimento: CedimentoTG
    schizzo: Sketch | None = campo_schizzo()
