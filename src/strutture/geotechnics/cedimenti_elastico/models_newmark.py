"""Pydantic I/O for `geo-cedimento-elastico-newmark`. Inputs flat, ordered as in the sheets
`Elastico_centrale_Newmark` (CENTRO) / `500` (PUNTO) top to bottom; outputs nested per
`docs/architecture-batch2.md` §1. Unit-neutral scalar fields + `unit_options` per user decision D1
(`docs/architecture-batch2.md` §9); the `strati` table stays SI (`boundary.py`)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.soil_layers import SoilLayer, strati_table_field

from .boundary import SistemaUnita
from .strati_contiguity import validate_ground_strati

ModalitaNewmark = Literal["CENTRO", "PUNTO"]

_LUNGHEZZA_OPTIONS = {"SI": "m", "tecnico": "cm"}
_PRESSIONE_OPTIONS = {"SI": "kPa", "tecnico": "kg/cm2"}


class NewmarkInput(BaseModel):
    model_config = ConfigDict(frozen=True, json_schema_extra={"unit_selector": "sistema_unita"})

    modalita: ModalitaNewmark = Field(
        default="CENTRO",
        description="Punto di verifica: centro fondazione (4 quadranti uguali) o punto arbitrario O",
        json_schema_extra={"symbol": "modalità", "group": "Modalità"},
    )
    sistema_unita: SistemaUnita = Field(default="SI", description="Sistema di unità di misura degli input dimensionali", json_schema_extra={"group": "Modalità"})
    q: float = Field(gt=0, description="Pressione di contatto uniforme in fondazione", json_schema_extra={"symbol": "q", "unit_options": _PRESSIONE_OPTIONS, "group": "Carico"})
    d: float = Field(ge=0, description="Profondità del piano di posa dal piano di campagna", json_schema_extra={"symbol": "D", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria"})
    b: float | None = Field(default=None, gt=0, description="Larghezza della fondazione (modalità CENTRO)", json_schema_extra={"symbol": "B", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria", "condition": {"field": "modalita", "equals": ["CENTRO"]}})
    l: float | None = Field(default=None, gt=0, description="Lunghezza della fondazione (modalità CENTRO)", json_schema_extra={"symbol": "L", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria", "condition": {"field": "modalita", "equals": ["CENTRO"]}})
    side_p: float | None = Field(default=None, gt=0, description="Lato O'd del rettangolo di confronto (modalità PUNTO)", json_schema_extra={"symbol": "O'd", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria (PUNTO)", "condition": {"field": "modalita", "equals": ["PUNTO"]}})
    side_q: float | None = Field(default=None, gt=0, description="Lato O'g del rettangolo di confronto (modalità PUNTO)", json_schema_extra={"symbol": "O'g", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria (PUNTO)", "condition": {"field": "modalita", "equals": ["PUNTO"]}})
    e1: float | None = Field(default=None, description="Distanza del punto O dal lato O'g, lungo O'd", json_schema_extra={"symbol": "e1", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria (PUNTO)", "condition": {"field": "modalita", "equals": ["PUNTO"]}})
    e2: float | None = Field(default=None, description="Distanza del punto O dal lato O'd, lungo O'g", json_schema_extra={"symbol": "e2", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Geometria (PUNTO)", "condition": {"field": "modalita", "equals": ["PUNTO"]}})
    strati: tuple[SoilLayer, ...] = strati_table_field(description="Stratigrafia del terreno, dal piano di campagna")
    z_max: float = Field(default=9.10, gt=0, description="Profondità massima di integrazione sotto il piano di posa", json_schema_extra={"symbol": "z_max", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Avanzate", "advanced": True})
    dz: float = Field(default=0.10, gt=0, description="Passo di discretizzazione in profondità", json_schema_extra={"symbol": "Δz", "unit_options": _LUNGHEZZA_OPTIONS, "group": "Avanzate", "advanced": True})
    legacy_compat: bool = Field(default=False, description="Riproduci il foglio Excel originale (errori inclusi)", json_schema_extra={"group": "Avanzate", "advanced": True})

    @model_validator(mode="after")
    def _valida_modalita(self) -> "NewmarkInput":
        if self.modalita == "CENTRO" and (self.b is None or self.l is None):
            raise ValueError("modalità CENTRO: indicare B e L")
        if self.modalita == "PUNTO" and None in (self.side_p, self.side_q, self.e1, self.e2):
            raise ValueError("modalità PUNTO: indicare O'd, O'g, e1 e e2")
        return self

    @model_validator(mode="after")
    def _stratigrafia_contigua(self) -> "NewmarkInput":
        validate_ground_strati(self.strati)
        return self


class CaricoNewmark(BaseModel):
    model_config = ConfigDict(frozen=True)

    q_kPa: float = Field(description="Pressione di contatto", json_schema_extra={"unit": "kPa", "symbol": "q"})
    d_m: float = Field(description="Profondità del piano di posa", json_schema_extra={"unit": "m", "symbol": "D"})


class RigaNewmark(BaseModel):
    model_config = ConfigDict(frozen=True)

    z_m: float = Field(description="Profondità sotto il piano di posa", json_schema_extra={"unit": "m", "symbol": "z"})
    delta_sigma_kPa: float = Field(description="Incremento di tensione verticale Δσz", json_schema_extra={"unit": "kPa", "symbol": "Δσz"})
    modulo_MPa: float | None = Field(description="Modulo elastico dello strato alla quota z (vuoto = fuori stratigrafia)", json_schema_extra={"unit": "MPa", "symbol": "E"})
    delta_w_m: float = Field(description="Contributo della fetta al cedimento", json_schema_extra={"unit": "m", "symbol": "Δw"})


class CentroCedimento(BaseModel):
    model_config = ConfigDict(frozen=True)

    w_centro_cm: float = Field(description="Cedimento elastico al centro fondazione", json_schema_extra={"unit": "cm", "symbol": "w", "highlight": True})
    w_centro_mm: float = Field(description="Cedimento elastico al centro fondazione", json_schema_extra={"unit": "mm", "symbol": "w"})
    w_qa_cm: float = Field(description="Cedimento di controllo (Ic di Boussinesq in forma chiusa)", json_schema_extra={"unit": "cm", "symbol": "w_QA"})
    scarto_qa_pct: float = Field(description="Scarto percentuale fra il cedimento principale e il controllo QA", json_schema_extra={"unit": "%", "symbol": "Δ%"})


class PuntoCedimento(BaseModel):
    model_config = ConfigDict(frozen=True)

    w_o_cm: float = Field(description="Cedimento elastico nel punto O", json_schema_extra={"unit": "cm", "symbol": "w_O", "highlight": True})
    w_o_mm: float = Field(description="Cedimento elastico nel punto O", json_schema_extra={"unit": "mm", "symbol": "w_O"})
    w_o_prime_cm: float = Field(description="Cedimento di riferimento nel vertice O' del rettangolo di confronto", json_schema_extra={"unit": "cm", "symbol": "w_O'"})
    w_o_prime_mm: float = Field(description="Cedimento di riferimento nel vertice O' del rettangolo di confronto", json_schema_extra={"unit": "mm", "symbol": "w_O'"})


class NewmarkOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    carico: CaricoNewmark
    righe: tuple[RigaNewmark, ...] = Field(
        description="Fette del percorso principale (centro in modalità CENTRO, punto O in modalità PUNTO)",
        json_schema_extra={"chart": {"x": "z_m", "y": ["delta_sigma_kPa"], "x_label": "z [m]", "y_label": "Δσz [kPa]"}},
    )
    righe_qa: tuple[RigaNewmark, ...] | None = Field(default=None, description="Fette del percorso di controllo QA (solo modalità CENTRO)")
    righe_o_prime: tuple[RigaNewmark, ...] | None = Field(default=None, description="Fette del percorso O' (solo modalità PUNTO)")
    centro: CentroCedimento | None = Field(default=None, description="Risultati (solo modalità CENTRO)")
    punto: PuntoCedimento | None = Field(default=None, description="Risultati (solo modalità PUNTO)")
