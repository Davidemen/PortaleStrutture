"""Input model for the `acciaio-colonna-h-ec3` tool (acciaio-colonne-ec3!Column check).

Fields follow the sheet top-to-bottom order (BUILD_CONTRACT: inputs stay flat). Section properties
(A, Iyy, Izz, Wel/Wpl, iy/iz, IT) are given as in the sheet, not recomputed from h/b/tw/tf/r — the
sheet itself never derives them from raw dimensions either (no root radius `r` cell exists on this
sheet: build/cellmaps/acciaio-colonne-ec3/column-check.txt has no `r` input, so none is added here).
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GradoAcciaioColonna = Literal["S235", "S275", "S355", "Q235", "Q345"]
TipoLavorazione = Literal["cold formed", "hot finished"]
ClasseSezione = Literal["class 1", "class 2", "class 3", "class 4"]
DiagrammaMomento = Literal["1", "2", "3a", "3b"]


class ColonnaEc3Input(BaseModel):
    """acciaio-colonne-ec3!Column check — H/I-section steel column, EN1993-1-1."""

    model_config = ConfigDict(frozen=True)

    sezione_nome: str = Field(default="", description="Denominazione della sezione", max_length=200, json_schema_extra={"group": "Geometria"})

    b_mm: float = Field(description="Larghezza base/ala della sezione", gt=0, le=5000, json_schema_extra={"unit": "mm", "symbol": "b", "group": "Geometria"})
    h_mm: float = Field(description="Altezza della sezione", gt=0, le=5000, json_schema_extra={"unit": "mm", "symbol": "h", "group": "Geometria"})
    tw_mm: float = Field(description="Spessore dell'anima", gt=0, le=200, json_schema_extra={"unit": "mm", "symbol": "t_w", "group": "Geometria"})
    tf_mm: float = Field(description="Spessore delle ali", gt=0, le=200, json_schema_extra={"unit": "mm", "symbol": "t_f", "group": "Geometria"})
    area_mm2: float = Field(description="Area lorda della sezione", gt=0, json_schema_extra={"unit": "mm2", "symbol": "A", "group": "Geometria"})
    grado_acciaio: GradoAcciaioColonna = Field(description="Grado dell'acciaio", json_schema_extra={"group": "Materiali"})
    gamma_m0: float | None = Field(
        default=None,
        description="Fattore parziale di sicurezza per la resistenza delle sezioni; vuoto = valore normativo EC3",
        gt=0,
        le=2,
        json_schema_extra={"unit": "-", "symbol": "γ_M0", "group": "Materiali", "advanced": True},
    )
    gamma_m1: float | None = Field(
        default=None,
        description="Fattore parziale di sicurezza per la resistenza all'instabilità; vuoto = valore normativo EC3",
        gt=0,
        le=2,
        json_schema_extra={"unit": "-", "symbol": "γ_M1", "group": "Materiali", "advanced": True},
    )
    tipo_lavorazione: TipoLavorazione = Field(description="Tipo di lavorazione della sezione (governa la curva di instabilità)", json_schema_extra={"group": "Geometria"})
    classe_sezione: ClasseSezione = Field(description="Classe della sezione trasversale", json_schema_extra={"group": "Geometria"})

    iyy_mm4: float = Field(description="Momento d'inerzia rispetto all'asse forte", gt=0, json_schema_extra={"unit": "mm4", "symbol": "I_yy", "group": "Geometria"})
    izz_mm4: float = Field(description="Momento d'inerzia rispetto all'asse debole", gt=0, json_schema_extra={"unit": "mm4", "symbol": "I_zz", "group": "Geometria"})
    wel_y_mm3: float = Field(description="Modulo di resistenza elastico, asse forte", gt=0, json_schema_extra={"unit": "mm3", "symbol": "W_el,y", "group": "Geometria"})
    wpl_y_mm3: float = Field(description="Modulo di resistenza plastico, asse forte", gt=0, json_schema_extra={"unit": "mm3", "symbol": "W_pl,y", "group": "Geometria"})
    wel_z_mm3: float = Field(description="Modulo di resistenza elastico, asse debole", gt=0, json_schema_extra={"unit": "mm3", "symbol": "W_el,z", "group": "Geometria"})
    wpl_z_mm3: float = Field(description="Modulo di resistenza plastico, asse debole", gt=0, json_schema_extra={"unit": "mm3", "symbol": "W_pl,z", "group": "Geometria"})
    it_mm4: float = Field(description="Momento d'inerzia torsionale", gt=0, json_schema_extra={"unit": "mm4", "symbol": "I_T", "group": "Geometria"})
    e_MPa: float = Field(description="Modulo elastico dell'acciaio", gt=0, json_schema_extra={"unit": "MPa", "symbol": "E", "group": "Materiali"})
    iy_mm: float = Field(description="Raggio d'inerzia, asse forte", gt=0, json_schema_extra={"unit": "mm", "symbol": "i_y", "group": "Geometria"})
    iz_mm: float = Field(description="Raggio d'inerzia, asse debole", gt=0, json_schema_extra={"unit": "mm", "symbol": "i_z", "group": "Geometria"})

    nsd_kN: float = Field(description="Sforzo normale di progetto", ge=0, json_schema_extra={"unit": "kN", "symbol": "N_sd", "group": "Azioni"})
    my_sd_kNm: float = Field(description="Momento flettente di progetto, asse forte", json_schema_extra={"unit": "kNm", "symbol": "M_y,sd", "group": "Azioni"}, ge=-1e5, le=1e5)
    mz_sd_kNm: float = Field(description="Momento flettente di progetto, asse debole", json_schema_extra={"unit": "kNm", "symbol": "M_z,sd", "group": "Azioni"}, ge=-1e5, le=1e5)
    vy_sd_kN: float = Field(description="Taglio di progetto sull'anima", ge=0, json_schema_extra={"unit": "kN", "symbol": "V_y,sd", "group": "Azioni"})
    vz_sd_kN: float = Field(description="Taglio di progetto sulle ali", ge=0, json_schema_extra={"unit": "kN", "symbol": "V_z,sd", "group": "Azioni"})

    lcr_yy_mm: float = Field(description="Lunghezza libera di inflessione, asse forte", gt=0, json_schema_extra={"unit": "mm", "symbol": "L_cr,yy", "group": "Geometria"})
    lcr_zz_mm: float = Field(description="Lunghezza libera di inflessione, asse debole", gt=0, json_schema_extra={"unit": "mm", "symbol": "L_cr,zz", "group": "Geometria"})
    ly_mm: float = Field(description="Lunghezza della colonna non deformata", gt=0, json_schema_extra={"unit": "mm", "symbol": "L_y", "group": "Geometria"})
    lt_mm: float = Field(description="Lunghezza libera di svergolamento", gt=0, json_schema_extra={"unit": "mm", "symbol": "l_T", "group": "Geometria"})
    c1: float = Field(description="Fattore del diagramma dei momenti per il momento critico elastico (tabella C1)", gt=0, le=10, json_schema_extra={"unit": "-", "symbol": "C_1", "group": "Azioni", "advanced": True})

    mj_y_kNm: float = Field(description="Momento secondario di estremità, asse forte", json_schema_extra={"unit": "kNm", "symbol": "M_j,y", "group": "Azioni"}, ge=-1e5, le=1e5)
    mj_z_kNm: float = Field(description="Momento secondario di estremità, asse debole", json_schema_extra={"unit": "kNm", "symbol": "M_j,z", "group": "Azioni"}, ge=-1e5, le=1e5)
    dmax_yy_mm: float = Field(
        default=0.0, description="Freccia massima per il diagramma dei momenti di tipo 2, asse forte",
        json_schema_extra={"unit": "mm", "symbol": "d_max,yy", "group": "Azioni", "condition": {"field": "diagramma_tipo_y", "equals": ["2"]}},
        ge=0, le=1000,
    )
    dmax_zz_mm: float = Field(
        default=0.0, description="Freccia massima per il diagramma dei momenti di tipo 2, asse debole",
        json_schema_extra={"unit": "mm", "symbol": "d_max,zz", "group": "Azioni", "condition": {"field": "diagramma_tipo_z", "equals": ["2"]}},
        ge=0, le=1000,
    )
    diagramma_tipo_y: DiagrammaMomento = Field(description="Tipo di diagramma dei momenti flettenti, asse forte", json_schema_extra={"group": "Azioni"})
    diagramma_tipo_z: DiagrammaMomento = Field(description="Tipo di diagramma dei momenti flettenti, asse debole", json_schema_extra={"group": "Azioni"})

    legacy_compat: bool = Field(default=False, description="Riproduci il foglio Excel originale (errori inclusi)", json_schema_extra={"group": "Avanzate", "advanced": True})
