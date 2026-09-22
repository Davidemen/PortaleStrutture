"""Campi di geometria di `SezioneMnInput`, in una classe base a parte per restare entro i 150
righe per modulo (regola dura 12); `SezioneMnInput` eredita da questa classe, quindi l'ordine dei
campi nello schema resta identico (i campi di geometria vengono per primi, come nel foglio)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .rows import MAX_VERTICI_ROWS, VerticeRow

Forma = Literal["rettangolare", "circolare", "a_t", "a_l", "parete", "poligono_libero"]


class GeometriaSezioneFields(BaseModel):
    """Forma della sezione trasversale e dimensioni condizionate dalla forma."""

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
