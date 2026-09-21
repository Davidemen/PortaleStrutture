"""Flat input model for `ca-sezione-dominio-mn` (docs/architecture-phase4.md §B): shape + conditional
dimensions, bars (table or parametric layout), materials, and the `azioni` combinations table.
Inputs stay flat (docs/BUILD_CONTRACT.md "Member tools"); only outputs are nested."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.materials.concrete import ConcreteClass
from strutture.shared.materials.rebar import RebarGrade
from strutture.shared.sezione_ca.modelli import LeggeAcciaio, LeggeCalcestruzzo
from strutture.shared.tabular import table_field

from .rows import MAX_AZIONI_ROWS, MAX_BARRE_ROWS, MAX_VERTICI_ROWS, AzioneRow, BarraRow, VerticeRow

Forma = Literal["rettangolare", "circolare", "a_t", "a_l", "parete", "poligono_libero"]
ArmaturaModo = Literal["tabella", "layout"]
LayoutTipo = Literal["fila_superiore", "fila_inferiore", "perimetrale", "circolare"]

_FORME_T_L: tuple[Forma, ...] = ("a_t", "a_l")
_LAYOUT_CON_N_BARRE: tuple[LayoutTipo, ...] = ("fila_superiore", "fila_inferiore", "circolare")
_LAYOUT_RETTANGOLARI_ARMATURA: tuple[LayoutTipo, ...] = ("fila_superiore", "fila_inferiore", "perimetrale")


class SezioneMnInput(BaseModel):
    """Forma + armatura + materiali di una sezione in c.a., e la tabella di combinazioni da
    verificare a pressoflessione (docs/architecture-phase4.md §B)."""

    model_config = ConfigDict(frozen=True)

    forma: Forma = Field(
        default="rettangolare", description="Forma della sezione trasversale",
        json_schema_extra={"group": "Geometria"},
    )
    b_mm: float | None = Field(
        default=None, gt=0, le=5000, description="Base della sezione rettangolare",
        json_schema_extra={"unit": "mm", "symbol": "b", "group": "Geometria",
                            "condition": {"field": "forma", "equals": ["rettangolare"]}},
    )
    h_mm: float | None = Field(
        default=None, gt=0, le=5000, description="Altezza della sezione (rettangolare, a T o a L)",
        json_schema_extra={"unit": "mm", "symbol": "h", "group": "Geometria",
                            "condition": {"field": "forma", "equals": ["rettangolare", "a_t", "a_l"]}},
    )
    diametro_mm: float | None = Field(
        default=None, gt=0, le=5000, description="Diametro della sezione circolare",
        json_schema_extra={"unit": "mm", "symbol": "D", "group": "Geometria",
                            "condition": {"field": "forma", "equals": ["circolare"]}},
    )
    bf_mm: float | None = Field(
        default=None, gt=0, le=5000, description="Larghezza della piattabanda/ala (sezione a T o a L)",
        json_schema_extra={"unit": "mm", "symbol": "b_f", "group": "Geometria",
                            "condition": {"field": "forma", "equals": ["a_t", "a_l"]}},
    )
    hf_mm: float | None = Field(
        default=None, gt=0, le=5000, description="Altezza della piattabanda/ala (sezione a T o a L)",
        json_schema_extra={"unit": "mm", "symbol": "h_f", "group": "Geometria",
                            "condition": {"field": "forma", "equals": ["a_t", "a_l"]}},
    )
    bw_mm: float | None = Field(
        default=None, gt=0, le=5000, description="Larghezza dell'anima/piedritto (sezione a T o a L)",
        json_schema_extra={"unit": "mm", "symbol": "b_w", "group": "Geometria",
                            "condition": {"field": "forma", "equals": ["a_t", "a_l"]}},
    )
    lw_mm: float | None = Field(
        default=None, gt=0, le=20000, description="Lunghezza della parete",
        json_schema_extra={"unit": "mm", "symbol": "l_w", "group": "Geometria",
                            "condition": {"field": "forma", "equals": ["parete"]}},
    )
    tw_mm: float | None = Field(
        default=None, gt=0, le=2000, description="Spessore corrente della parete",
        json_schema_extra={"unit": "mm", "symbol": "t_w", "group": "Geometria",
                            "condition": {"field": "forma", "equals": ["parete"]}},
    )
    le_mm: float | None = Field(
        default=None, gt=0, le=5000, description="Lunghezza degli elementi di estremità della parete",
        json_schema_extra={"unit": "mm", "symbol": "l_e", "group": "Geometria",
                            "condition": {"field": "forma", "equals": ["parete"]}},
    )
    te_mm: float | None = Field(
        default=None, gt=0, le=2000, description="Spessore degli elementi di estremità della parete",
        json_schema_extra={"unit": "mm", "symbol": "t_e", "group": "Geometria",
                            "condition": {"field": "forma", "equals": ["parete"]}},
    )
    vertici: tuple[VerticeRow, ...] = Field(
        default=(), max_length=MAX_VERTICI_ROWS,
        description="Vertici del contorno poligonale libero (minimo 3)",
        json_schema_extra={
            "group": "Geometria", "condition": {"field": "forma", "equals": ["poligono_libero"]},
            "widget": "table", "table": {"paste": True, "csv": False, "fixed_rows": False, "preview_rows": 50},
        },
    )
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
        if self.forma == "rettangolare" and (self.b_mm is None or self.h_mm is None):
            raise ValueError("sezione rettangolare: indicare base (b) e altezza (h)")
        if self.forma == "circolare" and self.diametro_mm is None:
            raise ValueError("sezione circolare: indicare il diametro")
        if self.forma in _FORME_T_L and (self.bf_mm is None or self.hf_mm is None or self.bw_mm is None or self.h_mm is None):
            raise ValueError("sezione a T/a L: indicare bf, hf, bw e h")
        if self.forma == "parete" and (self.lw_mm is None or self.tw_mm is None or self.le_mm is None or self.te_mm is None):
            raise ValueError("parete: indicare lw, tw, le e te")
        if self.forma == "poligono_libero" and len(self.vertici) < 3:
            raise ValueError("il contorno poligonale libero deve avere almeno 3 vertici")
        return self

    @model_validator(mode="after")
    def _valida_armatura(self) -> "SezioneMnInput":
        if self.armatura_modo == "tabella" and len(self.barre) == 0:
            raise ValueError("specificare almeno una barra di armatura")
        if self.armatura_modo == "layout":
            if self.layout_tipo is None or self.layout_copriferro_mm is None or self.layout_diametro_mm is None:
                raise ValueError("layout armatura: indicare tipo, copriferro e diametro")
            if self.layout_tipo in _LAYOUT_CON_N_BARRE and self.layout_n_barre is None:
                raise ValueError(f"layout '{self.layout_tipo}': indicare il numero di barre")
            if self.layout_tipo == "perimetrale" and self.layout_n_per_lato is None:
                raise ValueError("layout 'perimetrale': indicare il numero di barre per lato")
            if self.layout_tipo in ("fila_superiore", "fila_inferiore", "perimetrale") and self.forma != "rettangolare":
                raise ValueError(f"il layout '{self.layout_tipo}' richiede una sezione rettangolare")
            if self.layout_tipo == "circolare" and self.forma != "circolare":
                raise ValueError("il layout 'circolare' richiede una sezione circolare")
            self._valida_copriferro_layout()
        return self

    def _valida_copriferro_layout(self) -> None:
        """Il copriferro netto più mezzo diametro non deve raggiungere il semilato (layout
        rettangolari) o il raggio (layout circolare), altrimenti le barre cadrebbero oltre l'asse di
        simmetria e la fila si "specchia" silenziosamente restando comunque interna al contorno
        (nessun errore veniva sollevato: copriferro fino a 200 mm era accettato indipendentemente da
        b/h/D)."""
        messaggio = "copriferro troppo grande per la sezione: le barre cadrebbero oltre l'asse"
        margine_mm = self.layout_copriferro_mm + self.layout_diametro_mm / 2.0  # type: ignore[operator]
        rettangolare_pronta = self.layout_tipo in _LAYOUT_RETTANGOLARI_ARMATURA and self.b_mm is not None and self.h_mm is not None
        if rettangolare_pronta and margine_mm >= min(self.b_mm, self.h_mm) / 2.0:  # type: ignore[arg-type]
            raise ValueError(messaggio)
        if self.layout_tipo == "circolare" and self.diametro_mm is not None and margine_mm >= self.diametro_mm / 2.0:
            raise ValueError(messaggio)


# `table_field()` (shared.tabular) carries no `group` hint; every input needs one
# (docs/BUILD_CONTRACT.md "Batch 2"). Patched here rather than in the shared module.
_azioni_field = SezioneMnInput.model_fields["azioni"]
_azioni_field.json_schema_extra = {**(_azioni_field.json_schema_extra or {}), "group": "Azioni"}
SezioneMnInput.model_rebuild(force=True)
