"""Flat input model for `ca-sezione-dominio-mn` (docs/architecture-phase4.md §B): shape + conditional
dimensions, bars (table or parametric layout), materials, and the `azioni` combinations table.
Inputs stay flat (docs/BUILD_CONTRACT.md "Member tools"); only outputs are nested."""
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from strutture.shared.materials.concrete import ConcreteClass
from strutture.shared.materials.rebar import RebarGrade
from strutture.shared.sezione_ca.modelli import LeggeAcciaio, LeggeCalcestruzzo
from strutture.shared.tabular import table_field

from .geometria_fields import GeometriaSezioneFields
from .rows import MAX_AZIONI_ROWS, MAX_BARRE_ROWS, AzioneRow, BarraRow
from .validazione_geometria import valida_armatura, valida_geometria

ArmaturaModo = Literal["tabella", "layout"]
LayoutTipo = Literal["fila_superiore", "fila_inferiore", "perimetrale", "circolare"]


class SezioneMnInput(GeometriaSezioneFields):
    """Forma + armatura + materiali di una sezione in c.a., e la tabella di combinazioni da
    verificare a pressoflessione (docs/architecture-phase4.md §B)."""

    model_config = ConfigDict(frozen=True)

    armatura_modo: ArmaturaModo = Field(
        default="tabella", description="Modalità di inserimento dell'armatura: tabella di barre oppure layout parametrico",
        json_schema_extra={"group": "Armatura"},
    )
    barre: tuple[BarraRow, ...] = Field(
        default=(), max_length=MAX_BARRE_ROWS, description="Barre d'armatura (posizione e diametro)",
        json_schema_extra={
            "group": "Armatura", "condition": {"field": "armatura_modo", "equals": ["tabella"]},
            "widget": "table", "table": {"paste": True, "csv": True, "fixed_rows": False, "preview_rows": 50},
        },
    )
    layout_tipo: LayoutTipo | None = Field(
        default=None, description="Tipo di disposizione parametrica dell'armatura",
        json_schema_extra={"group": "Armatura", "condition": {"field": "armatura_modo", "equals": ["layout"]}},
    )
    layout_copriferro_mm: float | None = Field(
        default=None, gt=0, le=200, description="Copriferro netto dal filo di calcestruzzo",
        json_schema_extra={"unit": "mm", "symbol": "c", "group": "Armatura",
                            "condition": {"field": "armatura_modo", "equals": ["layout"]}},
    )
    layout_diametro_mm: float | None = Field(
        default=None, gt=0, le=60, description="Diametro delle barre del layout",
        json_schema_extra={"unit": "mm", "symbol": "φ", "group": "Armatura",
                            "condition": {"field": "armatura_modo", "equals": ["layout"]}},
    )
    layout_n_barre: int | None = Field(
        default=None, gt=0, le=200, description="Numero di barre (fila superiore/inferiore o disposizione circolare)",
        json_schema_extra={"symbol": "n", "group": "Armatura",
                            "condition": {"field": "layout_tipo", "equals": ["fila_superiore", "fila_inferiore", "circolare"]}},
    )
    layout_n_per_lato: int | None = Field(
        default=None, gt=0, le=50, description="Numero di barre per lato (layout perimetrale)",
        json_schema_extra={"symbol": "n_lato", "group": "Armatura",
                            "condition": {"field": "layout_tipo", "equals": ["perimetrale"]}},
    )
    classe_calcestruzzo: ConcreteClass = Field(
        default="C25/30", description="Classe di resistenza del calcestruzzo",
        json_schema_extra={"group": "Materiali"},
    )
    grado_acciaio: RebarGrade = Field(
        default="B450C", description="Classe di resistenza dell'armatura",
        json_schema_extra={"group": "Materiali"},
    )
    legge_calcestruzzo: LeggeCalcestruzzo = Field(
        default="parabola-rettangolo", description="Legge costitutiva del calcestruzzo",
        json_schema_extra={"group": "Materiali", "advanced": True},
    )
    legge_acciaio: LeggeAcciaio = Field(
        default="elastico-perfettamente-plastico", description="Legge costitutiva dell'acciaio",
        json_schema_extra={"group": "Materiali", "advanced": True},
    )
    azioni: tuple[AzioneRow, ...] = table_field(
        AzioneRow, max_rows=MAX_AZIONI_ROWS, min_rows=1, key="nome", paste=True, csv=True,
        description="Combinazioni di carico N-M da verificare (1-500 righe)",
    )

    @model_validator(mode="after")
    def _valida_geometria(self) -> "SezioneMnInput":
        valida_geometria(
            forma=self.forma, b_mm=self.b_mm, h_mm=self.h_mm, diametro_mm=self.diametro_mm,
            bf_mm=self.bf_mm, hf_mm=self.hf_mm, bw_mm=self.bw_mm, lw_mm=self.lw_mm, tw_mm=self.tw_mm,
            le_mm=self.le_mm, te_mm=self.te_mm, vertici=self.vertici,
        )
        return self

    @model_validator(mode="after")
    def _valida_armatura(self) -> "SezioneMnInput":
        valida_armatura(
            forma=self.forma, armatura_modo=self.armatura_modo, barre=self.barre, layout_tipo=self.layout_tipo,
            layout_copriferro_mm=self.layout_copriferro_mm, layout_diametro_mm=self.layout_diametro_mm,
            layout_n_barre=self.layout_n_barre, layout_n_per_lato=self.layout_n_per_lato,
            b_mm=self.b_mm, h_mm=self.h_mm, diametro_mm=self.diametro_mm,
        )
        return self


# `table_field()` (shared.tabular) carries no `group` hint; every input needs one
# (docs/BUILD_CONTRACT.md "Batch 2"). Patched here rather than in the shared module.
_azioni_field = SezioneMnInput.model_fields["azioni"]
_azioni_field.json_schema_extra = {**(_azioni_field.json_schema_extra or {}), "group": "Azioni"}
SezioneMnInput.model_rebuild(force=True)
