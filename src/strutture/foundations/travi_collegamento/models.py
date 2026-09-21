"""Input model for `fond-trave-collegamento` (one composed tool, `norma` switches NTC2018/EN1998).

Fields follow the sheets' top-to-bottom order (BUILD_CONTRACT: inputs stay flat). The two sheets
share most cells (section/material/force/span/stirrup inputs); `condition` hints show only the
fields relevant to the selected `norma`.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.materials.concrete import ConcreteClass
from strutture.shared.materials.rebar import RebarGrade

Norma = Literal["NTC2018", "EN1998"]
CategoriaSottosuoloTravi = Literal["A", "B", "C", "D"]  # Tabelle!M118:M121 / M131:M134 — no "E" row
CategoriaTopograficaTravi = Literal["T1", "T2", "T3", "T4"]  # Tabelle!M124:M127 (Tab. 3.2.V)


class TraviCollegamentoInput(BaseModel):
    """`Travi collegamento NTC2018` / `Travi colleg. EN 1998-1 e 5` — tie-beam axial force + section checks."""

    model_config = ConfigDict(frozen=True)

    norma: Norma = Field(default="NTC2018", description="Normativa di riferimento", json_schema_extra={"group": "Sito"})

    ag_g: float = Field(description="Accelerazione orizzontale massima al sito ag (C4)", gt=0, le=2, json_schema_extra={"unit": "g", "symbol": "a_g", "group": "Sito"})
    f0: float | None = Field(
        default=None, description="Fattore di amplificazione dello spettro F0 (C5)", gt=0, le=5,
        json_schema_extra={"unit": "-", "symbol": "F_0", "group": "Sito", "condition": {"field": "norma", "equals": ["NTC2018"]}},
    )
    categoria_sottosuolo: CategoriaSottosuoloTravi = Field(description="Categoria di sottosuolo (C6/C5)", json_schema_extra={"group": "Sito"})
    categoria_topografica: CategoriaTopograficaTravi | None = Field(
        default=None, description="Categoria topografica (C7)",
        json_schema_extra={"group": "Sito", "condition": {"field": "norma", "equals": ["NTC2018"]}},
    )
    ms: float | None = Field(
        default=None, description="Magnitudo di onde di superficie Ms (C6)", gt=0, le=10,
        json_schema_extra={"unit": "-", "symbol": "M_s", "group": "Sito", "condition": {"field": "norma", "equals": ["EN1998"]}},
    )

    b_mm: float = Field(description="Base della sezione della trave di collegamento B (C11/C9)", gt=0, le=5000, json_schema_extra={"unit": "mm", "symbol": "B", "group": "Geometria"})
    h_mm: float = Field(description="Altezza della sezione della trave di collegamento H (C12/C10)", gt=0, le=5000, json_schema_extra={"unit": "mm", "symbol": "H", "group": "Geometria"})
    phi_mm: float = Field(description="Diametro armature longitudinali φ (C13/C11)", gt=0, le=50, json_schema_extra={"unit": "mm", "symbol": "φ", "group": "Geometria"})
    n_barre: int = Field(description="Numero di barre longitudinali N. (C14/C12)", ge=1, le=100, json_schema_extra={"group": "Geometria"})

    classe_calcestruzzo: ConcreteClass = Field(description="Classe di resistenza del calcestruzzo (C17/C15)", json_schema_extra={"group": "Materiali"})
    classe_acciaio: RebarGrade = Field(description="Classe di resistenza dell'armatura (C18/C16)", json_schema_extra={"group": "Materiali"})

    n1_kN: float = Field(description="Forze verticali agenti sul primo plinto N1 (C22/C20)", ge=0, json_schema_extra={"unit": "kN", "symbol": "N_1", "group": "Azioni"})
    n2_kN: float = Field(description="Forze verticali agenti sul secondo plinto N2 (C23/C21)", ge=0, json_schema_extra={"unit": "kN", "symbol": "N_2", "group": "Azioni"})

    l_mm: float = Field(description="Luce netta della trave di collegamento l (C38/C36)", gt=0, le=50000, json_schema_extra={"unit": "mm", "symbol": "l", "group": "Geometria"})
    beta: float = Field(description="Coefficiente per la luce di libera inflessione β (C39/C37)", gt=0, le=2, json_schema_extra={"unit": "-", "symbol": "β", "group": "Geometria"})

    n_piani: int | None = Field(
        default=None, description="Numero di piani oltre il piano interrato (C49)", ge=0, le=200,
        json_schema_extra={"group": "Geometria", "condition": {"field": "norma", "equals": ["EN1998"]}},
    )

    phi_staffa_mm: float = Field(description="Diametro staffe φ (C48/C56)", gt=0, le=30, json_schema_extra={"unit": "mm", "symbol": "φ_st", "group": "Geometria"})
    n_bracci: int = Field(description="Bracci staffe N. (C49/C57)", ge=1, le=20, json_schema_extra={"group": "Geometria"})
    alpha_staffa_deg: float | None = Field(
        default=90.0, description="Inclinazione staffe α (C58)", gt=0, le=90,
        json_schema_extra={"unit": "°", "symbol": "α", "group": "Geometria", "condition": {"field": "norma", "equals": ["EN1998"]}},
    )
    cf_mm: float = Field(description="Copriferro cf (C50/C59)", gt=0, le=200, json_schema_extra={"unit": "mm", "symbol": "c", "group": "Geometria"})
    p_mm: float = Field(description="Passo staffe considerato p (C53/C62)", gt=0, le=1000, json_schema_extra={"unit": "mm", "symbol": "p", "group": "Geometria"})

    legacy_compat: bool = Field(default=False, description="Riproduci il foglio Excel originale (errori inclusi)", json_schema_extra={"group": "Avanzate", "advanced": True})

    @model_validator(mode="after")
    def _campi_richiesti_per_norma(self) -> "TraviCollegamentoInput":
        """NTC2018 needs F0 + categoria topografica; EN1998 needs Ms (Ms selects the spectrum type)."""
        if self.norma == "NTC2018" and (self.f0 is None or self.categoria_topografica is None):
            raise ValueError("F0 e categoria topografica sono richiesti per la normativa NTC2018")
        if self.norma == "EN1998" and self.ms is None:
            raise ValueError("La magnitudo Ms è richiesta per la normativa EN1998")
        return self
