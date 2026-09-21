"""Input model for `fond-plinto-su-pali` (docs/specs/fond-plinti-pali.md, 4 analyst tools composed
into one workflow). Fields follow the sheet's top-to-bottom order; the `reazioni` table follows
docs/architecture-batch2.md §2 (no `famiglia` split for pile caps, §9-D5)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.ec2_shear.v_rd_max import V_RD_MAX_COEFF_A1_2014
from strutture.shared.load_table import ReactionRow, reazioni_table_field, validate_unique_nodo_combo
from strutture.shared.materials.concrete import ConcreteClass
from strutture.shared.materials.rebar import RebarGrade
from strutture.shared.pile_group import SchemaPali

COEFF_VRD_MAX_DESCRIPTION = (
    "Coefficiente di vRd,max = c·ν·fcd: 0,4 (EN 1992-1-1/A1:2014, consigliato) oppure 0,5 "
    "(EN 1992-1-1:2004 con Appendice Nazionale italiana)"
)


class PlintoSuPaliInput(BaseModel):
    """`2xxxx_Plinti su pali_PL-FX_S&T Eurocode 2.xlsx` — pile cap by strut-and-tie, verified
    against a table of column reactions per load combination (LCC)."""

    model_config = ConfigDict(frozen=True)

    schema_pali: SchemaPali = Field(default="2x2", description="Schema geometrico dei pali in pianta",
                                     json_schema_extra={"group": "Geometria", "symbol": "-"})
    lx_m: float = Field(default=2.0, description="Interasse pali in direzione X", ge=0, le=20,
                         json_schema_extra={"unit": "m", "symbol": "L_X", "group": "Geometria"})
    ly_m: float = Field(default=2.0, description="Interasse pali in direzione Y", ge=0, le=20,
                         json_schema_extra={"unit": "m", "symbol": "L_Y", "group": "Geometria"})
    ax_m: float = Field(description="Dimensione in pianta del plinto lungo X", gt=0, le=20,
                         json_schema_extra={"unit": "m", "symbol": "A_X", "group": "Geometria"})
    by_m: float = Field(description="Dimensione in pianta del plinto lungo Y", gt=0, le=20,
                         json_schema_extra={"unit": "m", "symbol": "B_Y", "group": "Geometria"})
    h_plinto_m: float = Field(description="Altezza del plinto", gt=0, le=5,
                               json_schema_extra={"unit": "m", "symbol": "H", "group": "Geometria"})
    copriferro_cm: float = Field(description="Copriferro netto", gt=0, le=30,
                                  json_schema_extra={"unit": "cm", "symbol": "c", "group": "Geometria"})
    ex_m: float = Field(default=0.0, description="Eccentricità di carico applicata lungo X", ge=-10, le=10,
                         json_schema_extra={"unit": "m", "symbol": "e_X", "group": "Geometria", "advanced": True})
    ey_m: float = Field(default=0.0, description="Eccentricità di carico applicata lungo Y", ge=-10, le=10,
                         json_schema_extra={"unit": "m", "symbol": "e_Y", "group": "Geometria", "advanced": True})

    bx_pilastro_m: float = Field(description="Dimensione del pilastro in pianta lungo X", gt=0, le=5,
                                  json_schema_extra={"unit": "m", "symbol": "b_X", "group": "Pilastro"})
    by_pilastro_m: float = Field(description="Dimensione del pilastro in pianta lungo Y", gt=0, le=5,
                                  json_schema_extra={"unit": "m", "symbol": "b_Y", "group": "Pilastro"})

    diametro_pila_mm: float = Field(description="Diametro del palo", gt=0, le=3000,
                                     json_schema_extra={"unit": "mm", "symbol": "Ø_palo", "group": "Pali"})
    diametro_long_assunto_mm: float = Field(default=24.0, description="Diametro longitudinale assunto per l'altezza utile",
                                             gt=0, le=50, json_schema_extra={"unit": "mm", "group": "Pali", "advanced": True})
    av_mm: float = Field(default=120.0, description="Distanza ridotta av per il taglio (EC2 §6.2.2(6))",
                          gt=0, le=2000, json_schema_extra={"unit": "mm", "symbol": "a_v", "group": "Pali", "advanced": True})
    resistenza_pila_compressione_kN: float = Field(description="Resistenza ammissibile del palo a compressione",
                                                     gt=0, json_schema_extra={"unit": "kN", "group": "Pali"})
    resistenza_pila_trazione_kN: float | None = Field(
        default=None, description="Resistenza ammissibile del palo a trazione (richiesta se un palo risulta teso)",
        gt=0, json_schema_extra={"unit": "kN", "group": "Pali", "advanced": True},
    )

    carico_aggiuntivo_kN: float = Field(default=0.0, description="Carico permanente aggiuntivo sul plinto (rinterro, pavimentazioni)",
                                         ge=0, json_schema_extra={"unit": "kN", "group": "Carichi", "advanced": True})
    gamma_g1: float = Field(default=1.3, description="Coefficiente parziale γG1 per il peso proprio", gt=1, le=2,
                             json_schema_extra={"unit": "-", "symbol": "γ_G1", "group": "Carichi", "advanced": True})

    classe_calcestruzzo: ConcreteClass = Field(default="C25/30", description="Classe di resistenza del calcestruzzo",
                                                json_schema_extra={"group": "Materiali"})
    grado_acciaio: RebarGrade = Field(default="B450C", description="Classe di resistenza dell'armatura",
                                       json_schema_extra={"group": "Materiali"})
    gamma_s: float = Field(default=1.15, description="Coefficiente parziale dell'acciaio γs", gt=1, le=1.5,
                            json_schema_extra={"unit": "-", "symbol": "γ_s", "group": "Materiali", "advanced": True})
    gamma_c: float = Field(default=1.5, description="Coefficiente parziale del calcestruzzo γc", gt=1, le=1.6,
                            json_schema_extra={"unit": "-", "symbol": "γ_c", "group": "Materiali", "advanced": True})

    diametro_inf_x_mm: float = Field(default=24.0, description="Diametro armatura inferiore, direzione X-X", gt=0, le=40,
                                      json_schema_extra={"unit": "mm", "group": "Armatura inferiore"})
    passo_inf_x_mm: float = Field(default=100.0, description="Passo armatura inferiore, direzione X-X", gt=0, le=500,
                                   json_schema_extra={"unit": "mm", "group": "Armatura inferiore"})
    diametro_inf_y_mm: float = Field(default=24.0, description="Diametro armatura inferiore, direzione Y-Y", gt=0, le=40,
                                      json_schema_extra={"unit": "mm", "group": "Armatura inferiore"})
    passo_inf_y_mm: float = Field(default=100.0, description="Passo armatura inferiore, direzione Y-Y", gt=0, le=500,
                                   json_schema_extra={"unit": "mm", "group": "Armatura inferiore"})

    diametro_sup_x_mm: float = Field(default=20.0, description="Diametro armatura superiore, direzione X-X", gt=0, le=40,
                                      json_schema_extra={"unit": "mm", "group": "Armatura superiore", "advanced": True})
    passo_sup_x_mm: float = Field(default=200.0, description="Passo armatura superiore, direzione X-X", gt=0, le=500,
                                   json_schema_extra={"unit": "mm", "group": "Armatura superiore", "advanced": True})
    diametro_sup_y_mm: float = Field(default=20.0, description="Diametro armatura superiore, direzione Y-Y", gt=0, le=40,
                                      json_schema_extra={"unit": "mm", "group": "Armatura superiore", "advanced": True})
    passo_sup_y_mm: float = Field(default=200.0, description="Passo armatura superiore, direzione Y-Y", gt=0, le=500,
                                   json_schema_extra={"unit": "mm", "group": "Armatura superiore", "advanced": True})

    diametro_tirante_xy_mm: float = Field(default=32.0, description="Diametro barre del tirante diagonale XY (schema 2x2)",
                                           gt=0, le=40, json_schema_extra={"unit": "mm", "group": "Tiranti"})
    n_tirante_xy: int = Field(default=2, description="Numero di barre del tirante diagonale XY", ge=1, le=50,
                               json_schema_extra={"unit": "-", "group": "Tiranti"})
    diametro_tirante_x_mm: float = Field(default=24.0, description="Diametro barre del tirante lungo X", gt=0, le=40,
                                          json_schema_extra={"unit": "mm", "group": "Tiranti"})
    n_tirante_x: int = Field(default=8, description="Numero di barre del tirante lungo X", ge=1, le=50,
                              json_schema_extra={"unit": "-", "group": "Tiranti"})
    diametro_tirante_y_mm: float = Field(default=24.0, description="Diametro barre del tirante lungo Y", gt=0, le=40,
                                          json_schema_extra={"unit": "mm", "group": "Tiranti"})
    n_tirante_y: int = Field(default=8, description="Numero di barre del tirante lungo Y", ge=1, le=50,
                              json_schema_extra={"unit": "-", "group": "Tiranti"})

    reazioni: tuple[ReactionRow, ...] = reazioni_table_field(
        description="Reazioni in colonna per nodo e combinazione di carico (LCC)",
    )

    coeff_vrd_max: Literal[0.4, 0.5] = Field(
        default=V_RD_MAX_COEFF_A1_2014, description=COEFF_VRD_MAX_DESCRIPTION,
        json_schema_extra={"symbol": "c", "group": "Avanzate", "advanced": True},
    )
    legacy_compat: bool = Field(default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
                                 json_schema_extra={"group": "Avanzate", "advanced": True})

    @model_validator(mode="after")
    def _valida(self) -> "PlintoSuPaliInput":
        validate_unique_nodo_combo(self.reazioni)
        return self


# `reazioni_table_field()` (shared.load_table) carries no `group` hint (docs/BUILD_CONTRACT.md
# "Batch 2" requires one on every input); patched here rather than in the shared module.
_reazioni_field = PlintoSuPaliInput.model_fields["reazioni"]
_reazioni_field.json_schema_extra = {**(_reazioni_field.json_schema_extra or {}), "group": "Reazioni"}
PlintoSuPaliInput.model_rebuild(force=True)
